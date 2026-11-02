#!/usr/bin/env python3
"""Compare the 3D shader with independently projected plane corners (EGL).

Checks perspective direction, X/Y rotations, native Z/XY mapping, pivot,
transparency, back faces, near-camera clipping, and preview/export scales.
"""
import importlib.util
from pathlib import Path
import moderngl
import numpy as np

SPEC=importlib.util.spec_from_file_location('gpu',Path(__file__).with_name('check-fx-ports.py'))
GPU=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(GPU)


def homography(source,destination):
    rows=[];values=[]
    for (x,y),(u,v) in zip(source,destination):
        rows.extend([[x,y,1,0,0,0,-u*x,-u*y],[0,0,0,x,y,1,-v*x,-v*y]])
        values.extend([u,v])
    return np.append(np.linalg.solve(rows,values),1).reshape(3,3)


def reference(width,height,layer_size,pivot,depth,rx,ry,native,image):
    a,b=np.radians([rx,ry]);sx,cx=np.sin(a),np.cos(a);sy,cy=np.sin(b),np.cos(b)
    rotation=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]) @ np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    corners=np.array([[0,0],[1,0],[1,1],[0,1]],dtype=float)
    local=(corners-pivot)*layer_size*[1,-1]
    world=np.c_[local,np.zeros(4)]@rotation.T+[0,0,depth]
    projected=world[:,:2]*1000/(world[:,2:]+1000)/layer_size*[1,-1]+pivot
    transform=native @ homography(corners,projected) @ np.linalg.inv(native)
    y,x=np.mgrid[:height,:width]
    output=np.stack(((x+.5)/width,(y+.5)/height,np.ones_like(x)),axis=-1)
    coordinates=output@np.linalg.inv(transform).T
    uv=coordinates[...,:2]/coordinates[...,2:]
    valid=np.all((uv>=0)&(uv<=1),axis=-1)
    sample=uv*[width,height]-.5
    low=np.floor(sample).astype(int);weight=sample-low
    high=np.clip(low+1,[0,0],[width-1,height-1]);low=np.clip(low,[0,0],[width-1,height-1])
    top=image[low[...,1],low[...,0]]*(1-weight[...,0,None])+image[low[...,1],high[...,0]]*weight[...,0,None]
    bottom=image[high[...,1],low[...,0]]*(1-weight[...,0,None])+image[high[...,1],high[...,0]]*weight[...,0,None]
    return (top*(1-weight[...,1,None])+bottom*weight[...,1,None])*valid[...,None]


def matrix_uniform(program,name,matrix):
    expanded=np.eye(4,dtype='f4');expanded[np.ix_([0,1,3],[0,1,3])]=matrix
    program[name].write(expanded.tobytes())


def main():
    ctx=moderngl.create_standalone_context(backend='egl')
    path=GPU.ROOT/'patch/effects/internal-transform-3d.xml'
    program=ctx.program(vertex_shader=GPU.vertex_for(path),fragment_shader=GPU.desktop(GPU.CHECK.assemble(path)))
    vao=ctx.vertex_array(program,[])
    poses=[(0,0,0),(400,0,0),(-350,0,0),(0,35.3,0),(0,0,-42.7),
           (300,25.2,-40.3),(0,180,0),(0,0,180),(600,-22.1,65.3),
           (-500,35.3,45.6),(0,360,360)]
    native=np.array([[.85,-.2,.175],[.2,.85,-.025],[0,0,1]])
    total=0;worst=0
    for width,height in [(48,32),(96,64)]:
        y,x=np.mgrid[:height,:width]
        alpha=np.where((x-width*.5)**2+(y-height*.5)**2<height**2*.16,.5,1).astype('f4')
        image=np.stack((x/(width-1),y/(height-1),np.ones_like(x)*.25,alpha),axis=-1).astype('f4')
        image[...,:3]*=image[...,3:4]
        texture=ctx.texture((width,height),4,image.tobytes(),dtype='f4')
        texture.filter=(moderngl.LINEAR,moderngl.LINEAR);texture.repeat_x=texture.repeat_y=False;texture.use(0)
        framebuffer=ctx.simple_framebuffer((width,height),components=4,dtype='f4');framebuffer.use()
        program['inputImg.texture'].value=0
        if 'acScreenSize' in program:program['acScreenSize'].value=(width,height)
        program['acLayerSize'].value=(320,180)
        for mapping in [np.eye(3),native]:
            matrix_uniform(program,'acScreenToLayer',np.linalg.inv(mapping))
            matrix_uniform(program,'acLayerToScreen',mapping)
            for pixel_pivot in [(0,0),(27,-13)]:
                program['acLayerPivot'].value=pixel_pivot
                pivot=np.array([.5,.5])+np.array(pixel_pivot)/[320,180]*[1,-1]
                for depth,rx,ry in poses:
                    program['depth'].value=depth;program['rotateX'].value=rx;program['rotateY'].value=ry
                    vao.render(vertices=3)
                    result=np.frombuffer(framebuffer.read(components=4,dtype='f4'),dtype='f4').reshape(height,width,4)
                    expected=reference(width,height,[320,180],pivot,depth,rx,ry,mapping,image)
                    delta=float(np.max(np.abs(result-expected)))
                    assert np.all(np.isfinite(result)) and delta<.0002,(width,depth,rx,ry,pixel_pivot,delta)
                    assert np.all(result[...,:3]<=result[...,3:4]+.00001),'premultiplied alpha'
                    worst=max(worst,delta);total+=1
        matrix_uniform(program,'acScreenToLayer',np.eye(3));matrix_uniform(program,'acLayerToScreen',np.eye(3))
        program['acLayerPivot'].value=(0,0)
        for depth,rx,ry in [(-1000,0,0),(-1200,0,0),(0,90,0),(0,0,90)]:
            program['depth'].value=depth;program['rotateX'].value=rx;program['rotateY'].value=ry
            vao.render(vertices=3)
            result=np.frombuffer(framebuffer.read(components=4,dtype='f4'),dtype='f4')
            assert np.all(np.isfinite(result)) and np.max(np.abs(result))<.0001,(depth,rx,ry)
            total+=1
        framebuffer.release();texture.release()
    print(f'PASS {total} 3D projection comparisons; maximum RGBA difference {worst:.8f}')
    vao.release();program.release();ctx.release()


if __name__=='__main__':main()
