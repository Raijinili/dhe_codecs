import os, sys, os.path
from struct import *


class AFS_File:
    """Class representing an AFS container file object."""
    def __init__(self, infile):
        """Takes file object, returns AFS_File object.

        infile: file object, usually obtained via open command. Must be at least "rb" mode"""
        self.AFSFileName = os.path.basename(infile.name)
        self.fpath = os.path.abspath(infile.name)
        if not AFS_File.isAFSFile(infile):
            pass #we need to throw some sort of agreed upon error here
        infile.seek(4)
        self.fileCount = unpack("<I", infile.read(4))[0]
        self.fileInfo = []
        # get each file's offset and size
        for i in range(self.fileCount):
            self.fileInfo.append({})
            self.fileInfo[i]["dataOffset"], self.fileInfo[i]["dataRunLength"] = unpack("<II", infile.read(8))
        fileNamesOffset, fileNamesRunLength = unpack("<II", infile.read(8))
        infile.seek(fileNamesOffset)
        for i in range(self.fileCount):
            self.fileInfo[i]["fileName"] = infile.read(32).strip(b"\0").decode('ascii')
            self.fileInfo[i]["u"] = unpack("<IIII", infile.read(16))
        self.infile = infile
    def extractFiles(self, outputdirectory=None, extrainfo=False):
        """Extracts all files within to outputdirectory.
        
        outputdirectory: if not provided, will create new folder in current working directory.
        extrainfo: prints out status while processing file."""
        if outputdirectory is None:
            outputdirectory = self.AFSFileName.split(".")[0] + "_files"
        os.makedirs(outputdirectory, exist_ok=True)
        for i in range(self.fileCount):
            self.extractFile(i, outputdirectory=outputdirectory)
            if extrainfo:
                print("Outputting %s as %08X_%s to %s" % (self.fileInfo[i]["fileName"], self.fileInfo[i]["dataOffset"], self.fileInfo[i]["fileName"], outputdirectory)) 
    def extractFile(self, fileindex, outputdirectory='.', initialindex=0):
        """Extracts a single file from AFS.
        
        fileindex: index number of specific file to extract.
        ourputdirectory: current working directory by default.
        initialindex: Default zero, if default, 0 is first index, 1 is second, etc."""
        if not 0 <= fileindex - initialindex < self.fileCount:
            raise IndexError(fileindex - initialindex)
        os.makedirs(outputdirectory, exist_ok=True)
        file = self.fileInfo[fileindex - initialindex]
        self.infile.seek(file["dataOffset"])
        fn = "%08X_%s" % (file["dataOffset"], file["fileName"])
        data = self.infile.read(file["dataRunLength"])
        with open(os.path.join(outputdirectory, fn), "wb") as oot:
            oot.write(data)
    def info(self):
        """Prints out info about the AFS file and contained files"""
        parts = [_info_format % (self.AFSFileName, self.fileCount)]
        for i in range(self.fileCount):
            file = self.fileInfo[i]
            parts.append(_file_info_format % (i, file["fileName"], file["dataRunLength"], file["dataOffset"], file["u"][0], file["u"][1], file["u"][2], file["u"][3]))
        return ''.join(parts)
    @staticmethod
    def isAFSFile(infile):
        """Class method for detecting if infile is an AFS file"""
        infile.seek(0)
        identifier = unpack("BBBB", infile.read(4))
        if identifier == (0x41, 0x46, 0x53, 0x00):
            return True
        return False

    def close(self):
        if getattr(self, 'infile', None) is not None:
            self.infile.close()
        if getattr(self, 'outfile', None) is not None:
            self.outfile.close()
    def __del__(self):
        self.close()

_usage_message = """Usage: [python] %s [mode] [options] inputfile

Commands:
	E, e: default behavior: extracts all files in AFS
	I, i: print information and exit
	O, o: output files to specific directory (o directory)
	V, v: output extra information, only meaningful in extract mode (using e flag)
""" % sys.argv[0]
_info_format = """AFS Container "%s", %i files

   Index	                        Filename	      Size	    Offset	        U1	        U2	        U3	        U4
"""
_file_info_format = """%#8i	%32s	%#10i	%0#10X	%0#10X	%0#10X	%0#10X	%0#10X
"""


if __name__=="__main__":
    if len(sys.argv) < 2:
        print(_usage_message)
        exit()
