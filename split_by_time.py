#!/usr/bin/env python

import sys, getopt, errno
import time

from datetime import datetime, timedelta

start = time.time()

reads = list()

def ReadFastqFile(_inputFile):
	readsDict = dict()
	headerChar = '@'
	_inputFile.seek(0)
	count = -1
	for line in _inputFile:
		count += 1
		if count %4 != 0:
			continue
		readID = ((line.split()[0])[1:]).strip()
		start = line.find("start_time")
		start = line.find("=", start)
		if(start > 0):
			end = line.find(" ", start + 1)
			time = line[start + 1 : end]
			time = time.strip()
			try:
				dt = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ")
				readsDict[readID] = dt
			except (ValueError) as e:
				print e
				print "From string: " + time
		else:
			print "Warning, could not find start time in header for read " + readID + ".\n"
	return readsDict

inputfile = ''
chunk_time = 0
readsDict = dict()

try:
	opts, args = getopt.getopt(sys.argv[1:],"hi:t:",["ifile="])
except getopt.GetoptError:
	print("Option not recognised.")
	print("python split_by_time.py -i <inputfile>")
	print("python split_by_time.py -h for further usage instructions.")
	sys.exit(2)
for opt, arg in opts:
	if opt == "-h":
		print("split_by_time.py -i <inputfile>")
		print("-i <input file>\t\t\t\t Name of fasta or fastq file to analyse.")
		print("-t <interval> \t\t\t Write the reads to new files, one for each interval of time (in hours, >0).")
		sys.exit()
	elif opt in ("-i", "--ifile"):
		inputfile = arg
	elif opt in ("-t"):
		chunk_time = float(arg)

if inputfile == '' or chunk_time <= 0:
	print("You must specify -i and -t")
	print("split_by_time.py -i <input file> -t <interval>")
	sys.exit(2)

# try to open and read the file
try:
	with open(inputfile, 'r') as infile:
		readsDict = ReadFastqFile(infile)
except (OSError, IOError) as e: 
	if getattr(e, 'errno', 0) == errno.ENOENT:
		print("Could not find file " + inputfile)
	print(e)
	sys.exit(2)

times = readsDict.values()
times.sort()
startTime = times[0]
lastTime = times[len(times) - 1]
totalTime = lastTime - startTime

hours = totalTime.days * 24 + (totalTime.seconds / (60*60)) + 1
num_chunks = hours / chunk_time + 1
file_array = list()

filename = inputfile.split("/")[-1]
filename_fields = filename.split(".")

print "Total time for run: " + str(totalTime)
print "Number of chunks: " + str(num_chunks)

for i in xrange(int(num_chunks)):
	new_filename = filename_fields[0] + "_" + str(i * chunk_time) + "-" + str((i+1) * chunk_time) + "." + filename_fields[-1]
	file_array.append(open(new_filename, 'w'))
try:
	with open(inputfile, 'r') as infile:
		header = infile.readline()
		lines_for_read = 0
		if header[0] == '>':
			header_char = '>'
			lines_for_read = 2
		elif header[0] == '@':
			header_char = '@'
			lines_for_read = 4
		else:
			print("Error: " + infile.name + " does not appear to be in fasta/fastq format.")
			sys.exit(2)

		infile.seek(0)
		count = 0
		currentWriteFile = file_array[0]
		for line in infile:
			if count % lines_for_read == 0:
				readID = (line.split()[0])[1:]
				time = readsDict[readID]
				delta = time - startTime
				for i in xrange(int(num_chunks)):
					if delta < timedelta(hours = (i + 1) * chunk_time):
						currentWriteFile = file_array[i]
						break
			currentWriteFile.write(line)
			count += 1
except (OSError, IOError) as e: 
	if getattr(e, 'errno', 0) == errno.ENOENT:
		print("Could not find file " + inputfile)
	print(e)
	sys.exit(2)

for i in xrange(int(num_chunks)):
	file_array[i].close()

end = time.time()