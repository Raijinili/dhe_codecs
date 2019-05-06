import os, sys, zlib
from struct import *


class DAR_File:
    def __init__(self, *, file=None, filename=None, create=None):
        """Returns DAR_File object representing a DAR container file.

        Keyword Arguments:
        file: a file object created with the open command and "rb" (minimum) access.
        filename: a filename string pointing to a DAR file, unnecessary if infile is provided."""
        if file is not None or filename is not None:
            self.infile = file or open(filename, "rb")
            if not DAR_File.isDARFile(self.infile):
                pass # we need to throw some sort of error here
            self.DARFileName = self.infile.name.split(os.sep)[-1]
            self.infile.seek(0)
            self.fileCount, self.fileDataOffset, self.fileNamesOffset, self.fileInfoOffset = unpack("<IIII", self.infile.read(16))
            self.fileInfo = []
            for i in range(self.fileCount):
                self.infile.seek(self.fileInfoOffset + (16 * i))
                self.fileInfo.append({})
                filenameOffset, self.fileInfo[i]["compressedSize"], self.fileInfo[i]["fileSize"], self.fileInfo[i]["fileOffset"] = unpack("<IIII", self.infile.read(16))
                self.infile.seek(filenameOffset)
                if self.fileInfo[i]["compressedSize"] != 0: self.fileInfo[i]["compressed"] = True
                else: self.fileInfo[i]["compressed"] = False
                # if anyone knows how to read inderterminate length, null-terminated strings from a binary file better than this, please change it!
                # possible - read all the strings in one go and split the giant string at each \x00
                self.fileInfo[i]["fileName"] = ""
                self.longestFileName = 0
                l = 0
                c = self.infile.read(1)
                while c != '\x00':
                    self.fileInfo[i]["fileName"] = self.fileInfo[i]["fileName"] + c
                    l += 1
                    c = self.infile.read(1)
                if l > self.longestFileName: self.longestFileName = l
            self.outfile = None
        else: # make a DAR file
            self.outfile = open(create, "wb")
            self.infile = None
    def extractFiles(self, directory=None):
        """Extracts all files from DAR archive.

        Keyword Arguments:
        directory: the directory to output the files too. If it doesn't exist, it will be created. Defaults to the DAR file's name."""
        if not directory:
            directory = self.DARFileName.split('.')[0]
        os.makedirs(directory, exist_ok=True)
        for i in range(self.fileCount):
            self.extractFile(i, 0, directory)
    def extractFile(self, fileindex, initialindex=0, directory=""):
        """Extracts the file at fileindex.

        Arguments:
        fileindex: the index of the particular file to extract.

        Keyword Arguments:
        initialindex: if not using zero indexing, pass the first index here. Defaults to zero.
        directory: where to save the extracted file. Defaults to current directory."""
        # does this default to the CWD or the directory in which the DAR is stored - experiments are necessary!
        fi = fileindex - initialindex
        self.infile.seek(self.fileInfo[fi]["fileOffset"])
        fa = self.fileInfo[fi]["fileName"].split('/')
        fn = directory
        if len(fa) > 1:
            for d in fa[:-1]:
                fn = os.path.join(fn, d)
                os.makedirs(fn, exist_ok=True)
        fn = os.path.join(fn, "%08X_%s" % (self.fileInfo[fi]["fileOffset"], fa[-1]))
        ofile = open(fn, "wb")
        if self.fileInfo[fi]["compressed"]:
            try:
                data = zlib.decompress(self.infile.read(self.fileInfo[fi]["compressedSize"]))
            except zlib.error:
                print("File at index %i (from initial index %i) failed to decompress despite appearing to be compressed. Outputting (compressed?) data to %s" % (fileindex, initialindex, fn))
                self.infile.seek(self.fileInfo[fi]["fileOffset"])
                data = self.infile.read(self.fileInfo[fi]["compressedSize"])
        else:
            data = self.infile.read(self.fileInfo[fi]["fileSize"])
        ofile.write(data)
        ofile.close()
    def addFiles(self, *args, **kwargs):
        pass #will likely rely on addFile() like the extraction methods do
    def addFile(self, *args, **kwargs):
        pass # DARS are probably the easiest to create with the least unknowns floating about them
    def info(self):
        """info() -> string
        
        Returns formatted string of information on DAR_File object."""
        l = self.longestFileName - 8
        if l < 8: l = 8
        parts = [infostr_format % (self.DARFileName, self.fileCount, self.fileDataOffset, self.fileInfoOffset, self.fileNamesOffset, " " * l)]
        for i in range(self.fileCount):
            file = self.fileInfo[i]
            if file["compressed"]: ss = file["compressedSize"]
            else: ss = file["fileSize"]
            parts.append(_file_info_format % (i, file["fileName"], file["compressed"], ss, file["fileSize"], file["fileOffset"]))
        return ''.join(parts)
    @staticmethod
    def isDARFile(infile):
        return False #for now

infostr_format = """DAR Container: "%s", %i files
File Data: %0#10X, File Descriptors: %0#10X, Filenames: %0#10X

   Index	%sFilename	Compressed	Stored Size	 Full Size	    Offset
"""
_file_info_format = """%#8i	%"+str(l+8)+"s	%10s	%0#10X	 %0#10X	%0#10X
"""


if __name__=="__main__":
    pass
