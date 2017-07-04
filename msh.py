import sys
import numpy as np
import itertools

class Mesh:

    keywords = ["Vertices", "Triangles", "Quadrilaterals","Tetrahedra","SolAtVertices"]

    def analyse(self, index, line):
        for k,kwd in enumerate(self.keywords):
            if self.found[k] and kwd not in self.done:
                self.numItems[k] = int(line)
                self.offset += self.numItems[k]
                self.found[k] = False
                self.done.append(kwd)
                return 1
            if kwd in line:
                if kwd not in self.done and line[0]!="#":
                    self.begin[k] = index+3 if kwd=="SolAtVertices" else index+2
                    self.found[k] = True
    def get_infos(self, path):
        for j in range(len(self.keywords)):
            with open(path) as f:
                f.seek(0)
                for i,l in enumerate(f):
                    if i>self.offset:
                        if self.analyse(i,l):
                            break
    def readArray(self,f, ind, dim, dt=None):
        try:
            f.seek(0)
            X = " ".join([l for l in itertools.islice(f, self.begin[ind], self.begin[ind] + self.numItems[ind])])
            if dt:
                return np.fromstring(X, sep=" ", dtype=dt).reshape((self.numItems[ind],dim))
            else:
                return np.fromstring(X, sep=" ").reshape((self.numItems[ind],dim))
        except:
            #print "Invalid format", ind, dim
            f.seek(0)
            try:
                for i in range(self.begin[ind]):
                    f.readline()

                arr = []
                for l in f:
                    if len(l.strip())>0:
                        arr.append([int(x) for x in l.strip().split()])
                    else:
                        break
                return np.array(arr,dtype=dt)
            except:
                print "Did not manage to read the array"
                sys.exit()
            sys.exit()
    def readSol(self,path=None):
        if self.path and not path:
            self.offset=0
            self.get_infos(self.path[:-5]+".sol")
            with open(self.path[:-5]+".sol") as f:
                    if self.numItems[4]:
                        #Try to read a single float solution file
                        try:
                            f.seek(0)
                            self.scalars = np.array([float(l) for l in itertools.islice(f, self.begin[4], self.begin[4] + self.numItems[4])])
                            self.solMin = np.min(self.scalars)
                            self.solMax = np.max(self.scalars)
                        except:
                            self.scalars=np.array([])
                        #Try to read a vector
                        try:
                            f.seek(0)
                            self.vectors = np.array([ [float(x) for x in l.strip().split()[:3]] for l in itertools.islice(f, self.begin[4], self.begin[4] + self.numItems[4])])
                            self.vecMin = np.min(np.linalg.norm(self.vectors,axis=1))
                            self.vecMax = np.min(np.linalg.norm(self.vectors,axis=1))
                        except:
                            self.vectors=np.array([])
                        #Try to read a scalar after a vector
                        try:
                            f.seek(0)
                            self.scalars = np.array([float(l.split()[3]) for l in itertools.islice(f, self.begin[4], self.begin[4] + self.numItems[4])])
                            self.solMin = np.min(self.scalars)
                            self.solMax = np.max(self.scalars)
                        except:
                            self.scalars=np.array([])
                    else:
                        self.scalars = np.array([])
                        self.vectors = np.array([])

    def __init__(self, path=None, cube=None):
        if cube:
            self.verts = np.array([
                [cube[0], cube[2], cube[4]],
                [cube[0], cube[2], cube[5]],
                [cube[1], cube[2], cube[4]],
                [cube[1], cube[2], cube[5]],
                [cube[0], cube[3], cube[4]],
                [cube[0], cube[3], cube[5]],
                [cube[1], cube[3], cube[4]],
                [cube[1], cube[3], cube[5]]
            ])
            self.tris = np.array([
                [0,1,2],
                [1,3,2],
                [4,6,5],
                [5,6,7],
                [1,5,3],
                [3,5,7],
                [2,6,4],
                [0,2,4],
                [3,7,6],
                [2,3,6],
                [0,4,1],
                [1,4,5]
            ])
            self.verts = np.insert(self.verts,3,0,axis=1)
            self.tris  = np.insert(self.tris,3,0,axis=1)
            self.quads=np.array([])
            self.tets=np.array([])
            self.computeBBox()
        elif path:
            self.done     = []
            self.found    = [False for k in self.keywords]
            self.begin    = [0 for k in self.keywords]
            self.numItems = [0 for k in self.keywords]
            self.offset   = 0

            self.path = path
            self.get_infos(path)
            with open(path) as f:
                if self.numItems[0]:
                    self.verts = self.readArray(f,0,4,np.float)
                if self.numItems[1]:
                    self.tris  = self.readArray(f,1,4,np.int)
                    self.tris[:,:3]-=1
                else:
                    self.tris = np.array([])
                if self.numItems[2]:
                    self.quads = self.readArray(f,2,5,np.int)
                    self.quads[:,:4]-=1
                else:
                    self.quads = np.array([])
                if self.numItems[3]:
                    self.tets  = self.readArray(f,3,5,np.int)
                    self.tets[:,:4]-=1
                else:
                    self.tets = np.array([])
            self.computeBBox()
        else:
            self.verts=np.array([])
            self.tris=np.array([])
            self.quads=np.array([])
            self.tets=np.array([])
        self.scalars=np.array([])
        self.vectors=np.array([])

    def caracterize(self):
        print "File " + self.path
        if len(self.verts):
            print "\tVertices:        ", len(self.verts)
            print "\tBounding box:    ", "[%.2f, %.2f] [%.2f, %.2f] [%.2f, %.2f]" % (self.xmin, self.xmax,self.ymin, self.ymax, self.zmin, self.zmax)
        if len(self.tris):
            print "\tTriangles:       ", len(self.tris)
        if len(self.quads):
            print "\tQuadrilaterals:  ", len(self.quads)
        if len(self.tets):
            print "\tTetrahedra:      ", len(self.tets)
        if len(self.scalars):
            print "\tScalars:         ", len(self.scalars)
        if len(self.vectors):
            print "\tVectors:         ", len(self.vectors)
    def computeBBox(self):
        self.xmin, self.ymin, self.zmin = np.amin(self.verts[:,:3],axis=0)
        self.xmax, self.ymax, self.zmax = np.amax(self.verts[:,:3],axis=0)
        self.dims = np.array([self.xmax - self.xmin, self.ymax - self.ymin, self.zmax - self.zmin])
        self.center = np.array([self.xmin + (self.xmax - self.xmin)/2, self.ymin + (self.ymax - self.ymin)/2, self.zmin + (self.zmax - self.zmin)/2])
    def fondre(self, otherMesh):
        off = len(self.verts)
        if len(otherMesh.tris)>0:
            self.tris  = np.append(self.tris,  otherMesh.tris + [off, off, off, 0],  axis=0)
        if len(otherMesh.tets)>0:
            self.tets  = np.append(self.tets,  otherMesh.tets + [off, off, off, off, 0],  axis=0)
        if len(otherMesh.quads)>0:
            self.quads = np.append(self.quads, otherMesh.quads + [off, off, off, off, 0], axis=0)
        if len(otherMesh.verts)>0:
            self.verts = np.append(self.verts, otherMesh.verts, axis=0)
    def replaceRef(self, oldRef, newRef):
        if len(self.tris)!=0:
            self.tris[self.tris[:,-1]==oldRef,-1] = newRef
        if len(self.quads)!=0:
            self.quads[self.quads[:,-1]==oldRef,-1] = newRef
        if len(self.tets)!=0:
            self.tets[self.tets[:,-1]==oldRef,-1] = newRef
    def removeRef(self, ref, keepTris=False, keepTets=False, keepQuads=False):
        if len(self.tris)!=0 and not keepTris:
            self.tris = self.tris[self.tris[:,-1]!=ref]
        if len(self.quads)!=0 and not keepQuads:
            self.quads = self.quads[self.quads[:,-1]!=ref]
        if len(self.tets)!=0 and not keepTets:
            self.tets = self.tets[self.tets[:,-1]!=ref]
    def scale(self,sc,center=[]):
        if len(center)>0:
            self.verts[:,:3] -= center
        else:
            self.verts[:,:3] -= self.center
        self.verts[:,:3] *= sc
        if len(center)>0:
            self.verts[:,:3] += center
        else:
            self.verts[:,:3] += self.center
        self.computeBBox()
    def inflate(self,sc):
        self.verts[:,:3] -= self.center
        self.verts[:,:3] += sc/np.linalg.norm(self.verts[:,:3],axis=1)[:,None] * self.verts[:,:3]
        self.verts[:,:3] += self.center
        self.computeBBox()
    def fitTo(self, otherMesh, keepRatio=True):
        otherDim = [
            otherMesh.dims[0]/self.dims[0],
            otherMesh.dims[1]/self.dims[1],
            otherMesh.dims[2]/self.dims[2]
        ]
        if keepRatio:
            scale = np.min(otherDim)
        else:
            scale = otherDim
        self.verts[:,:3]-=self.center
        self.verts[:,:3]*=scale
        self.verts[:,:3]+=otherMesh.center
        self.computeBBox()
    def discardUnused(self):
        used = np.zeros(shape=(len(self.verts)),dtype="bool_")
        if len(self.tris)>0:
            used[np.ravel(self.tris[:,:3])]=True
        if len(self.tets)>0:
            used[np.ravel(self.tets[:,:4])]=True
        newUsed = np.cumsum(used)
        self.verts = self.verts[used==True]
        if len(self.scalars)>0:
            self.scalars = self.scalars[used==True]
        if len(self.tris)>0:
            newTris = np.zeros(shape=(len(self.tris),4),dtype=int)
            newTris[:,-1] = self.tris[:,-1]
            for i,triangle in enumerate(self.tris):
                for j,t in enumerate(triangle[:-1]):
                    newTris[i,j] = newUsed[t]-1
            self.tris = newTris
        if len(self.tets)>0:
            newTets = np.zeros(shape=(len(self.tets),5),dtype=int)
            newTets[:,-1] = self.tets[:,-1]
            for i,tet in enumerate(self.tets):
                for j,t in enumerate(tet[:-1]):
                    newTets[i][j] = newUsed[t]-1
            self.tets = newTets
        self.computeBBox()

    def getHull(self):
        with open("tmp.node","w") as f:
            f.write( str(len(self.verts)) + " 3 0 0\n")
            for i,v in enumerate(self.verts):
                f.write(str(i+1) + " " + " ".join([str(x) for x in v]) + "\n")
        import os
        os.system("tetgen -cAzn tmp.node > /dev/null 2>&1")

        neigh = []
        with open("tmp.1.neigh") as f:
            for l in f.readlines()[1:-1]:
                neigh.append( [int(l.split()[i]) for i in range(1,5)] )
        tets = []
        with open("tmp.1.ele") as f:
            for l in f.readlines()[1:-1]:
                tets.append( [int(l.split()[i]) for i in range(1,5)] )
        verts = []
        with open("tmp.1.node") as f:
            for l in f.readlines()[1:-1]:
                verts.append( [float(l.split()[i]) for i in range(1,4)]+[0] )
        tris = []
        for i,n in enumerate(neigh):
            for j,c in enumerate(n):
                if c==-1:
                    tris.append([tets[i][k] for k in range(4) if k!=j]+[0])
        refs = [1 for t in tris]

        mesh = Mesh()
        mesh.verts = np.array(verts)
        mesh.tris  = np.array(tris,dtype=int)
        mesh.discardUnused()
        mesh.computeBBox()

        return mesh


    def writeArray(self, path, head, array, form, firstOpening=False, incrementIndex=False):
        if len(array):
            if firstOpening:
                f = path
            else:
                f = open(path,"a")
            if incrementIndex:
                array = np.copy(array)
                array[:,:-1]+=1
            np.savetxt(
                f,
                array,
                fmt=form,
                newline="\n",
                header=head,
                footer=" ",
                comments=""
            )
    def write(self, path):
        self.writeArray(path, "MeshVersionFormatted 2\nDimension 3\n\nVertices\n"+str(len(self.verts)), self.verts, '%.8f %.8f %.8f %i', firstOpening=True)
        self.writeArray(path, "Triangles\n"+str(len(self.tris)), self.tris, '%i %i %i %i', incrementIndex=True)
        self.writeArray(path, "Quadrilaterals\n"+str(len(self.quads)), self.quads, '%i %i %i %i %i', incrementIndex=True)
        self.writeArray(path, "Tetrahedra\n"+str(len(self.tets)), self.tets, '%i %i %i %i %i', incrementIndex=True)
        with open(path,"a") as f:
            f.write("\nEnd")
    def writeSol(self,path):
        self.writeArray(path,"MeshVersionFormatted 2\nDimension 3\n\nSolAtVertices\n"+str(len(self.scalars))+"\n1 1", self.scalars, '%.8f', firstOpening=True)
