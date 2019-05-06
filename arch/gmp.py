import sys, os, zlib, os.path
from struct import *


verbose = False


class GMP_File:
    def __init__(self, infile):
        """Class representing the GMP archive format."""
        self.GMPFileName = os.path.basename(infile.name)
        self.fpath = os.path.abspath(infile.name)
        infile.seek(0)
        self.fileCount, self.descriptorOffset, self.unknown0, self.unknown1 = unpack("<IIII", infile.read(16))
        self.fileDescriptors = []
        for i in range(self.fileCount):
            infile.seek(self.descriptorOffset + i * 32)
            self.fileDescriptors.append({});
            self.fileDescriptors[i]["name"] = infile.read(20).strip(b"\0").decode('ascii')
                #^ Should that be 0x20?
            #Guarding against null file names:
            if not self.fileDescriptors[i]["name"]:
                self.fileDescriptors[i]["name"] = "f" + str(i)
            self.fileDescriptors[i]["rl"], self.fileDescriptors[i]["offset"], self.fileDescriptors[i]["unknown"] = unpack("<III", infile.read(12))
        self.infile = infile
    def extractFiles(self, outputdirectory=None):
        """Extract all files contained within the GMP file to a folder outputdirectory.

        outputdirectory: a directory name or location for files. If not provided, then use f"{GMPFileName}_files".
        """
        if outputdirectory is None:
            outputdirectory = self.GMPFileName + "_files"
        if self.infile.closed:
            try:
                self.infile = open(self.fpath, 'rb')
            except IOError:
                raise IOError(self.fpath + " was closed, and we couldn't reopen it. Quitting...")
        os.makedirs(outputdirectory, exist_ok=True)
        for i in range(self.fileCount):
            self.infile.seek(self.fileDescriptors[i]["offset"])
            filedata = self.infile.read(self.fileDescriptors[i]["rl"])
            if verbose:
                print("Writing file %(name)s (unknown descriptor: %(unknown)08x)" % self.fileDescriptors[i])
            with open(os.path.join(outputdirectory, self.fileDescriptors[i]["name"]), "wb") as oot:
                oot.write(filedata)
    def info(self):
        """Return a string containing information on the file represented by this object."""
        parts = [_info_format % (self.fileCount, self.descriptorOffset, self.unknown0, self.unknown1, "Filename", "Size", "Offset")]
        for i in range(self.fileCount):
            parts.append(_file_info_format % self.fileDescriptors[i])
        return ''.join(parts)

    def close(self):
        if getattr(self, 'infile', None) is not None:
            self.infile.close()
        if getattr(self, 'outfile', None) is not None:
            self.outfile.close()
    def __del__(self):
        self.close()


_usage_message = """Usage:	[python] %s [options] file.gmp

Options: 
	O, o directory: output files to directory. Values containing separators will be interpreted as absolute paths.
	V, v: verbose, output some extra information
""" % sys.argv[0]

_info_format = """Files: %d	Descriptor offset: %08x	Unknown 1: %08x	Uknown 2: %08x

%20s	%8s	%8s
"""

_file_info_format = """%(name)20s	%(rl)08x	%(offset)08x
"""

if __name__=="__main__":
    if len(sys.argv) < 2:
        print(_usage_message)
        exit()
    else:
        od = ""
        filegiven = False
        for i in range(len(sys.argv[2:])):
            if sys.argv[i] in ['o', 'O']:
                od = sys.argv[i+1]
                i += 1
            elif sys.argv[i] in ['v', 'V']:
                verbose = True
            else:
                inpath = sys.argv[i]
                filegiven = True
        if not filegiven:
            print(_usage_message)
            exit()
    with open(inpath, 'rb') as infile:
        gmp = GMP_File(infile)
        if verbose:
            print(gmp.info())
            print("Extracting files...")
            print()
        if od != "":
            gmp.extractFiles(od)
        else:
            gmp.extractFiles()


