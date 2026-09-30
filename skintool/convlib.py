import numpy as np, sys
from PIL import Image
import os
_M=os.path.join(os.path.dirname(os.path.abspath(__file__)),'mesh')
P=np.load(os.path.join(_M,'P.npy'));UV=np.load(os.path.join(_M,'UV.npy'));IB=np.load(os.path.join(_M,'IB.npy'))
def boxes(slim=True):
    aw=3 if slim else 4
    return {'head':(0,0,8,8,8),'torso':(16,16,8,12,4),'rarm':(40,16,aw,12,4),'larm':(32,48,aw,12,4),'rleg':(0,16,4,12,4),'lleg':(16,48,4,12,4)}
OVLB={'head':(32,0),'torso':(16,32),'rarm':(40,32),'larm':(48,48),'rleg':(0,32),'lleg':(0,48)}
SLOTBOX=boxes(True)  # slot geometry (mesh arms are 3px wide)
# ---- mesh faces (plane groups of triangles) ----
def slot_of(r):
    cx=(r[0]+r[2])/2; cy=(r[1]+r[3])/2
    for n,(U,V,w,h,d) in SLOTBOX.items():
        for (x,y,rw,rh) in ((U+d,V,2*w,d),(U,V+d,2*d+2*w,h)):
            if x<=cx<=x+rw and y<=cy<=y+rh: return n,'base'
    if cx>=32 and cy<16: return 'head','hat'
    return None,None
raw=[]
groups={}
for a,b,c in IB:
    q=P[[a,b,c]]; n=np.cross(q[1]-q[0],q[2]-q[0]); n=n/np.linalg.norm(n); ax=int(np.argmax(abs(n)))
    # connected plane groups: key by axis, plane coordinate and uv island via rounded uv bbox later
    groups.setdefault((ax,round(float(q[0][ax]),0)),[]).append((a,b,c))
# split each plane group into uv-connected islands (faces)
faces=[]
for (ax,pl),tris in groups.items():
    par={}
    def f(x):
        while par.setdefault(x,x)!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for t in tris:
        par[f(t[0])]=f(t[1]); par[f(t[1])]=f(t[2])
    isl={}
    for t in tris: isl.setdefault(f(t[0]),[]).append(t)
    for ts in isl.values():
        vv=sorted({v for t in ts for v in t}); uv=UV[vv]; pos=P[vv]
        r=(uv[:,0].min(),uv[:,1].min(),uv[:,0].max(),uv[:,1].max())
        if (r[2]-r[0])<0.5 or (r[3]-r[1])<0.5: continue   # eye/mouth strips handled separately
        if abs(r[2]-r[0]-2)<0.3 and r[3]<8.5 and r[2]<9: continue
        slot,layer=slot_of(r)
        if slot is None: continue
        faces.append(dict(slot=slot,layer=layer,ax=ax,vv=vv,ts=ts,r=r,pos=pos,uv=uv))
# slot bbox (by layer) for fractions
sb={}
for F in faces:
    k=(F['slot'],F['layer']); lo,hi=F['pos'].min(0),F['pos'].max(0)
    if k in sb: sb[k]=(np.minimum(sb[k][0],lo),np.maximum(sb[k][1],hi))
    else: sb[k]=(lo,hi)
def geo_part(slot,layer):
    lo,hi=sb[(slot,layer)]; c=(lo+hi)/2
    if slot=='head': return 'head'
    if slot=='torso': return 'torso'
    if slot in('rarm','larm'): return 'rarm' if c[0]<0 else 'larm'
    return 'rleg' if c[0]<0 else 'lleg'          # mesh x<0 = character's right
for F in faces:
    F['part']=geo_part(F['slot'],F['layer'])
    lo,hi=sb[(F['slot'],F['layer'])]; c=(lo+hi)/2
    F['lo'],F['hi']=lo,hi
    F['side']='max' if F['pos'][:,F['ax']].mean()>c[F['ax']] else 'min'
    A=np.c_[F['uv'],np.ones(len(F['uv']))]; F['M']=np.linalg.lstsq(A,F['pos'],rcond=None)[0]
    F['flip']=bool(F['ax']==1 and ((F['M'][0,0]>0)!=(F['side']=='max')))
def jsrc(part,slim,ax,side,pos,lo,hi,dU=0,dV=0,flip=False):
    U,V,w,h,d=boxes(slim)[part]; U+=dU; V+=dV
    fr=lambda i:min(max((pos[i]-lo[i])/(hi[i]-lo[i]),0),1)
    if ax==1:
        fx,fz=fr(0),fr(2)
        if side=='max': return (U+d+(1-fx if flip else fx)*w,V+d+(1-fz)*h)
        return (U+2*d+w+(fx if flip else 1-fx)*w,V+d+(1-fz)*h)
    if ax==0:
        fy,fz=fr(1),fr(2)
        return (U+fy*d,V+d+(1-fz)*h) if side=='min' else (U+d+w+(1-fy)*d,V+d+(1-fz)*h)
    fx,fy=fr(0),fr(1)
    return (U+d+fx*w,V+fy*d) if side=='max' else (U+d+w+fx*w,V+(1-fy)*d)
def prepare(java,slim):
    """flatten java: overlays -> base. returns base RGBA float array(64,64,4) and hat RGBA (for head 'hat' layer)"""
    J=np.array(java.convert('RGBA')).astype(float)
    if J.shape[0]==32: raise SystemExit('legacy 64x32 skin not supported')
    def comp(dst,ov):
        a=ov[...,3:4]/255.0; return np.concatenate([dst[...,:3]*(1-a)+ov[...,:3]*a,np.maximum(dst[...,3:4],ov[...,3:4])],-1)
    return J
def sample(J,u,v):
    return J[min(max(int(np.floor(v+1e-6)),0),63),min(max(int(np.floor(u+1e-6)),0),63)]
ICON_DY=0   # смещение иконки по вертикали (строки атласа); 0 = как в нативных текстурах
def convert(java,slim=True,hide_eyes=True,native=None):
    J=prepare(java,slim)
    out=np.zeros((64,64,4),np.uint8) if native is None else native.copy()
    filled=np.zeros((64,64),bool)
    for F in faces:
        x0,y0,x1,y1=[int(round(v)) for v in F['r']]
        for ty in range(y0,y1):
            for tx in range(x0,x1):
                pos=np.array([tx+0.5,ty+0.5,1.0])@F['M']
                if F['layer']=='hat':
                    u,v=jsrc(F['part'],slim,F['ax'],F['side'],pos,F['lo'],F['hi'],32,0,flip=F['flip'])
                    c=sample(J,u-1e-4*0,v).copy()
                    c=sample(J,u,v).copy()
                    if 0<c[3]<255: c[3]=0          # semi-transparent hat texels are flattened into the base
                    out[ty,tx]=c.astype(np.uint8)
                else:
                    u,v=jsrc(F['part'],slim,F['ax'],F['side'],pos,F['lo'],F['hi'],flip=F['flip'])
                    c=sample(J,u,v).copy()
                    ox,oy=OVLB[F['part']]; bx,by=boxes(slim)[F['part']][:2]
                    o=sample(J,*jsrc(F['part'],slim,F['ax'],F['side'],pos,F['lo'],F['hi'],ox-bx,oy-by,flip=F['flip'])) if F['part']!='head' else None
                    if F['part']=='head':
                        o=sample(J,*jsrc(F['part'],slim,F['ax'],F['side'],pos,F['lo'],F['hi'],32,0,flip=F['flip']))
                        if o[3]==255: o=np.zeros(4)   # opaque hat stays in the hat shell
                    a=o[3]/255.0
                    c[:3]=c[:3]*(1-a)+o[:3]*a; c[3]=255 if c[3]>0 else 255
                    out[ty,tx]=c.astype(np.uint8)
                filled[ty,tx]=True
    # hide game eyes / mouth / brows: small stray quads at x<=8,y<8 (not part of the cube islands)
    # portrait icon (8x8 at 56,20): face + full hat composite
    base=np.array(java.convert('RGBA')).astype(float)
    face=base[8:16,8:16].copy(); hat=base[8:16,40:48]; a=hat[...,3:4]/255.0
    ic=face[...,:3]*(1-a)+hat[...,:3]*a
    y0=20+ICON_DY; out[y0:y0+8,56:64,:3]=ic.astype(np.uint8); out[y0:y0+8,56:64,3]=255   # икона героя: 8x8 ровно в (56..63, 20..27) - проверено маркерным тестом в игре
    # native texels outside every cube island = game eyes/brows/mouth quads (+ portrait icon, rebuilt above)
    if native is not None:
        stray=(native[...,3]>0)&~filled
        stray[19:29,56:64]=False
        keep=np.zeros_like(stray); keep[0:8,0:10]=True; stray&=keep
        if hide_eyes: out[stray]=0
    return out,filled
if False:
    print(len(faces),'faces'); 
    for F in faces: print(F['slot'],F['layer'],F['part'],F['ax'],F['side'],[round(x) for x in F['r']])
