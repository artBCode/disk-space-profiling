# disk-space-profiling
This script finds the folders that occupy most of the disk space and the type of files(extention based) that they contain.

Example of usage:
```
checkDiskUsage.py /a/folder/ --max_depth_details 7 --min_size_folder 3 --min_size_extension 0.5 --output_file disk_usage.csv
```

This is how the generated file disk_usage.csv looks like:

```
#Folder                                                 DiskSpace(G)	extention=space				
/Applications/Xcode.app/Contents/Developer/Platforms	6.949   None=2.297	dat=0.845
/Applications/Xcode.app/Contents/Developer              9.261	None=2.527	.LINK=0.861	dat=0.845	dylib=0.658	png=0.512
/Applications/Xcode.app/Contents                        10.151	None=2.885	.LINK=1.084	dat=0.845	dylib=0.684	png=0.514
/Applications/Xcode.app                                 10.151  None=2.885	.LINK=1.084	dat=0.845	dylib=0.684	png=0.514
/Applications                                           15.924	None=4.247	.LINK=1.872	dylib=1.264	dat=0.899	png=0.798
```
