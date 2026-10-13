import sys, zlib, struct
from twofish import Twofish
KEY=bytes([0x89]*16); IV=bytes([0x10]*16)
tf=Twofish(KEY)
E=tf.encrypt
def xor(a,b): return bytes(x^y for x,y in zip(a,b))
def dbl(b):
    n=int.from_bytes(b,'big')<<1
    if n>>128: n=(n&((1<<128)-1))^0x87
    return n.to_bytes(16,'big')
L=E(bytes(16)); K1=dbl(L); K2=dbl(K1)
def cmac(m):
    blocks=[m[i:i+16] for i in range(0,len(m),16)] or [b'']
    last=blocks[-1]
    if len(last)==16: last=xor(last,K1)
    else: last=xor(last+b'\x80'+bytes(15-len(last)),K2)
    blocks[-1]=last; c=bytes(16)
    for b in blocks: c=E(xor(c,b))
    return c
def omac(t,m): return cmac(bytes(15)+bytes([t])+m)
def ctr(n,data):
    c=int.from_bytes(n,'big'); out=bytearray()
    for i in range(0,len(data),16):
        ks=E(c.to_bytes(16,'big')); c=(c+1)%(1<<128)
        out+=xor(data[i:i+16],ks)
    return bytes(out)
def eax_dec(ct):
    data,tag=ct[:-16],ct[-16:]
    N=omac(0,IV); H=omac(1,b''); C=omac(2,data)
    if xor(xor(N,H),C)!=tag: print("WARN tag mismatch",file=sys.stderr)
    return ctr(N,data)
def eax_enc(pt):
    N=omac(0,IV); H=omac(1,b''); data=ctr(N,pt); C=omac(2,data)
    return data+xor(xor(N,H),C)
def decode(raw):
    n=len(raw)
    s1=bytes(raw[n-1-i]^((n-i*n)&0xff) for i in range(n))
    s2=eax_dec(s1); m=len(s2)
    s3=bytes(s2[i]^((m-i)&0xff) for i in range(m))
    return zlib.decompress(s3[4:])
def encode(xml):
    s3=struct.pack('>I',len(xml))+zlib.compress(xml)
    m=len(s3); s2=bytes(s3[i]^((m-i)&0xff) for i in range(m))
    s1=eax_enc(s2); n=len(s1); out=bytearray(n)
    for i in range(n): out[n-1-i]=s1[i]^((n-i*n)&0xff)
    return bytes(out)
if __name__ == "__main__":
    mode,src,dst=sys.argv[1:4]
    d=open(src,'rb').read()
    open(dst,'wb').write(decode(d) if mode=='d' else encode(d))
