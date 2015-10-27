__author__ = 'skywal'
from collections import defaultdict
import os,re,argparse,operator,sys,subprocess

parser = argparse.ArgumentParser(description='Disk space profiling')
parser.add_argument('topFolder', type=str,help='the folder we want to profile')
parser.add_argument('--max_depth_details','-mdd', type=int,help='How deep we want to know the file dettails',default=sys.maxint)
parser.add_argument('--output_file','-of', type=str,help='The output file',default="disk_space_summary.csv")
parser.add_argument('--measurement_unit','-mu', type=str,help='The output file',choices={'B','K','M','G'},default="M")



args = parser.parse_args()

MEASUREMENT={"K":1024,"M":1048576,"G":1073741824,"":1,"b":1}
DIR_KEY='.DIR'
LINK_KEY='.LINK'
class Folder:
    def __init__(self,name,parent=""):
        self.parent=parent
        self.name=name
        self.typeSpace=defaultdict(int)
        self.subdirs=[]
        dir_only_size=os.path.getsize(os.path.join(parent,name))
        self.typeSpace[DIR_KEY] += dir_only_size
        self.totalSize=dir_only_size



    def fullPath(self):
        return os.path.join(self.parent,self.name)
    def updateSpace(self,typeSpace):
        for ext in typeSpace:
            self.typeSpace[ext] +=typeSpace[ext]
            self.totalSize += typeSpace[ext]
    def addFileSize(self,extention,size):
        self.typeSpace[extention] += size
        self.totalSize += size

    def getTotalSize(self,unit=""):
        return float(self.totalSize)/(MEASUREMENT[unit])

    def getFileSizesStr(self,unit):
        fl=[]
        for extention,size in sorted(self.typeSpace.items(), key=operator.itemgetter(1),reverse=True):
            fl.append("%s=%.3f" % (extention,float(size)/MEASUREMENT[unit]))
        return (",".join(fl))



    def printTree(self,unit="",maxDepth=sys.maxint):
        def recursivePrint(folder,depthLeft):
            print "%s\t:\t%s" %(folder.getTotalSize(unit),os.path.join(folder.parent,folder.name))
            for subdir in sorted(folder.subdirs,key=operator.attrgetter("totalSize")):
                if depthLeft>0:
                    recursivePrint(subdir,depthLeft-1)

        recursivePrint(self, maxDepth)
    def toString(self,unit):
        return "%.3f,%s" %(self.getTotalSize(unit),self.getFileSizesStr(unit))
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback ):
        return True


def memory_usage_ps():
    out = subprocess.Popen(['ps', 'v', '-p', str(os.getpid())],
    stdout=subprocess.PIPE).communicate()[0].split(b'\n')
    vsz_index = out[0].split().index(b'RSS')
    mem = float(out[1].split()[vsz_index]) / 1024
    return mem



def navigate(topFolder,max_depth_dettails,measurementUnit,logFileDescr):
    def recursive_navigate(currentFolder,depthLeft):

        full_path_curr=currentFolder.fullPath()


        try:
            fileAndDirs=os.listdir(full_path_curr)
        except:
            print "WARNING: Problems listing the content of %s" % full_path_curr
            fileAndDirs=[]
        for fd in fileAndDirs:
            full_path_sub=os.path.join(full_path_curr,fd)
            if os.path.isfile(full_path_sub):
                fileSize=os.path.getsize(full_path_sub)
                m=re.search("\.([^.]+)$",fd)
                extention=None
                if m!=None:
                    extention=m.group(1).lower()
                currentFolder.addFileSize(extention,fileSize)
            elif os.path.isdir(full_path_sub):
                subDir=Folder(fd,full_path_curr)
                recursive_navigate(subDir,depthLeft-1)
                currentFolder.updateSpace(subDir.typeSpace)
                #currentFolder.subdirs.append(subDir) # keep track of the tree


            elif os.path.islink(fd):
                linkSize=os.path.getsize(full_path_sub)
                currentFolder.addFileSize(LINK_KEY,linkSize)
            dettails_c_f=currentFolder.toString(measurementUnit)
            #print dettails_c_f
            logFileDescr.write("%s\n" % (dettails_c_f))
    recursive_navigate(topFolder,max_depth_dettails)



topFolder=Folder(args.topFolder)

log=open(args.output_file,"w")
navigate(topFolder,args.max_depth_details,args.measurement_unit,log)
log.close()

