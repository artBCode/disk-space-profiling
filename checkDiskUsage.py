#!/usr/bin/env python2.7
__author__ = 'artBCode'
from collections import defaultdict
import os,re,argparse,operator,sys,subprocess

folderCountCompleted=0

parser = argparse.ArgumentParser(description='Disk space profiling. For each folder it logs the amount of space used by different types of files(identified by extension).',epilog="Example:%s /one/folder --max_depth_details 7 --min_size_folder 3" % sys.argv[0])
parser.add_argument('topFolder', type=str,help='the folder we want to profile')
parser.add_argument('--max_depth_details','-mdd', type=int,help='How deep we want to know the file dettails',default=sys.maxint)
parser.add_argument('--output_file','-of', type=str,help='The output csv file in which the profiling data will be written',default="disk_space_summary.csv")
parser.add_argument('--min_size_folder','-msf', type=float,help='If a folder has less than this ammount it will not be logged even if it is within max_depth_details.',default=0)
parser.add_argument('--measurement_unit','-mu', type=str,help='The output file',choices={'B','K','M','G'},default="G")
parser.add_argument('--status_freq','-sf', type=int,help='The frequency of status messages. Every x folders it analyses.',default=10000)
parser.add_argument('--min_size_extension','-mse', type=float,help='It logs into the csv file only the file data types that occupy more than this.',default=0)
parser.add_argument('--max_no_columns','-mnc', type=int,help='Maximum number of file extentions the script should log for each folder. The LibbreOffice supports up to 1024.',default=100)



args = parser.parse_args()

MEASUREMENT={"K":1024,"M":1048576,"G":1073741824,"":1,"B":1}
DIR_KEY='.DIR'
LINK_KEY='.LINK'
class Folder:
	def __init__(self,name,parent=""):
		self.parent=parent
		self.name=name
		self.typeSpace=defaultdict(int)
		self.subdirs=[]
		try:
			dir_only_size=os.path.getsize(os.path.join(parent,name))
		except:
			print "Cannot get the size of %s" % os.path.join(parent,name) # handles the case when the dir is deleted during runtime
			dir_only_size=0        
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

	def getFileSizesStr(self,unit,maximum_columns):
		fl=[]
		counter=0
		for extention,size in sorted(self.typeSpace.items(), key=operator.itemgetter(1),reverse=True):
			extension_size=float(size)/MEASUREMENT[unit]
			if extension_size < args.min_size_extension:
				continue
			fl.append("%s=%.3f" % (extention,extension_size))
			if counter > maximum_columns:
				break
			counter += 1
		return (",".join(fl))



	def printTree(self,unit="",maxDepth=sys.maxint):
		def recursivePrint(folder,depthLeft):
			print "%s\t:\t%s" %(folder.getTotalSize(unit),os.path.join(folder.parent,folder.name))
			for subdir in sorted(folder.subdirs,key=operator.attrgetter("totalSize")):
				if depthLeft>0:
					recursivePrint(subdir,depthLeft-1)

		recursivePrint(self, maxDepth)
	def toString(self,unit,maximum_no_columns):
		return "%s,%.3f,%s" % (self.fullPath(),self.getTotalSize(unit),self.getFileSizesStr(unit,maximum_no_columns))
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
		global folderCountCompleted
		full_path_curr=currentFolder.fullPath()


		try:
			fileAndDirs=os.listdir(full_path_curr)
		except:
			print "WARNING: Problems listing the content of %s" % full_path_curr
			fileAndDirs=[]
		for fd in fileAndDirs:
			full_path_sub=os.path.join(full_path_curr,fd)
			if os.path.islink(full_path_sub):
				try:
					linkSize=os.path.getsize(full_path_sub)
					currentFolder.addFileSize(LINK_KEY,linkSize)
					#print "Skipped link %s" % full_path_sub
				except:
					print "Cannot get the size of %s" % full_path_sub
				continue
			if os.path.isfile(full_path_sub):
				try:
					fileSize=os.path.getsize(full_path_sub)
					m=re.search("\.([^.]+)$",fd)
					extention=None
					if m!=None:
						extention=m.group(1).lower()
					currentFolder.addFileSize(extention,fileSize)
				except:
					print "Cannot get the size of %s" % full_path_sub
			elif os.path.isdir(full_path_sub):
				subDir=Folder(fd,full_path_curr)
				recursive_navigate(subDir,depthLeft-1)
				currentFolder.updateSpace(subDir.typeSpace)
				folderCountCompleted +=1
				if folderCountCompleted % args.status_freq ==0:
					print "Folder %s: Current RAM usage=%s MB" % (folderCountCompleted,memory_usage_ps())
				#currentFolder.subdirs.append(subDir) # keep track of the tree


		if depthLeft>=0 and (args.min_size_folder==0 or (args.min_size_folder!=0 and currentFolder.totalSize/MEASUREMENT[args.measurement_unit] > args.min_size_folder)):
			dettails_c_f=currentFolder.toString(measurementUnit,args.max_no_columns)
			#print dettails_c_f
			logFileDescr.write("%s\n" % (dettails_c_f))
	recursive_navigate(topFolder,max_depth_dettails)


if not os.path.isdir(args.topFolder):
	print "Error: The top folder %s is missing" % args.topFolder
	exit(1)

topFolder=Folder(args.topFolder)

log=open(args.output_file,"w")
log.write("#Folder,DiskSpace(%s),extention=space\n" % args.measurement_unit)
navigate(topFolder,args.max_depth_details,args.measurement_unit,log)
log.close()

