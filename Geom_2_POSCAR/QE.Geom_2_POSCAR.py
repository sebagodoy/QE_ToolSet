#! /usr/bin/env python3

################################################################
#
#	QE.Geom_to_POSCAR.py
#
#	Function: 	reads geometries from QuantumEspresso input files
#				and produces POSCAR VASP-type files that can be
#				easyly read with codes such as VESTA and vmd
#
#	Version:	1.0 - 30/08/2021
#
#	Comments:	Works for .in files, recognice automatic .out
#				and extract from .out in process.
#	To do:		Check geometry from output and all factors
# 				involved that are missing
# 				Check atoms in cell
#
#	Made by Sebastian Godoy
#	GitHub repository: https://github.com/sebagodoy/QE_ToolSet
#
################################################################

print('\n'+' '*4+'Create VASP-type POSCAR from QuantumEspresso files\n')

#### Tools
def CodeStatus(iStr, **kwargs):
	print(' '*8+'> '+str(iStr), **kwargs)
def CodeError(iStr, **kwargs):
	quit('\n'+' '*8+'!'*40+' '*10+'Exit by error: '+iStr+'\n'+' '*8+'!'*40, **kwargs)

def FixNum(iNum, Ndec=14):
	formatstr = '{:.'+str(Ndec)+'f}'
	return str(formatstr.format(iNum))
def FixNumExp(iNum, Ndec=14):
	formatstr = '{:.'+str(Ndec)+'E}'
	return str(formatstr.format(iNum))
def FixStrLead(iStr, Length):
	return ' '*(Length-len(iStr))+iStr

def SepareInputSection(FileStr, SectionStr):
	Section = [i.strip() for i in FileStr.split(SectionStr)[1].split('/')[0].replace('\n', ',').split(',')]
	while "" in Section: Section.remove("")
	return Section


######## Get file: Atom coordinates
iFileName = str(input('    Input geometry file : '))
# Test
# iFileName = 'TiO2PG.in'


# Opening
try:
	CodeStatus('Opening file', end=' ... ')
	with open(iFileName, 'r') as f:
		iFile = f.read()
		f.close() # Not nedded but good practice
	print('found it!')
except:
	CodeError('File not found, byyyeeee!')

# Identify file type: Input/Output
try:
	CodeStatus('Checking file', end=' ... ')
	if ('&system' in iFile and 'CELL_PARAMETERS' in iFile and 'ATOMIC_POSITIONS' in iFile):
		FileType='Input'

	if 'This program is part of the open-source Quantum ESPRESSO suite' in iFile:
		FileType = 'Output'

	print(FileType)
except:
	CodeError('What a weird file, u sure is the right one?')






# Getting Data: base
LatParam = 1.0
NAtoms = 0
CellVectors = []
AtomDict = {}

if FileType == 'Input':

	# Getting header sections
	Sect_System = SepareInputSection(iFile, '&system')
	for i in Sect_System:
		if 'nat' in i: NAtoms = int(i.split('=')[1])

	# Searching file for data
	iFileLines = iFile.split('\n')
	i=0
	while i < len(iFileLines):

		## Section: Cell
		if 'CELL_PARAMETERS' in iFileLines[i]:
			CodeStatus('Getting Cell vectors', end=' ... ')
			# Check units
			if not 'angstrom' in  iFileLines[i]: CodeError('Cell units not programed yet')
			for j in range(3):
				i+=1
				CellVectors.append([float(k) for k in iFileLines[i].split()])
			print('Ok')

		## Section: Atoms
		if 'ATOMIC_POSITIONS' in iFileLines[i]:
			for j in range(NAtoms):
				# Next atom line
				i+=1
				Atomtype = iFileLines[i].split()[0]
				AtomCoord = [float(k) for k in iFileLines[i].split()[1:]]
				# Add New Atom type to registry
				if not Atomtype in AtomDict: AtomDict[Atomtype] = []
				# Add Atom to registry
				AtomDict[Atomtype].append(AtomCoord)

		## Next line
		i+=1



elif FileType == 'Output':
	# Searching in file
	iFileLines = iFile.split('\n')
	i=0
	while i < len(iFileLines) and i>-1:

		## Lattice Parameter
		if 'lattice parameter (alat)' in iFileLines[i]:
			Angstrom_2_AU = 1.8897259885789			# Factor desde google
			# Angstrom_2_AU = 1.8897259885789004	# Factor comparando .in con .out
			# Angstrom_2_AU = 1.889723441460845		# Factor comparando .in con .out
			LatParam = float(iFileLines[i].split()[4])/Angstrom_2_AU
			CodeStatus('Lattice parameter = '+str(FixNum(LatParam, 8))+' Angstrom')

		## Cell vectors
		if 'crystal axes: (cart. coord. in units of alat)' in iFileLines[i]:
			CodeStatus('Getting and adapting cell vectors', end=' ... ')
			for j in range(3):
				i+=1
				CellVectors.append([float(k)*LatParam for k in iFileLines[i].split()[3:6]])
			print('Ok')

		## Number of atoms
		if 'number of atoms/cell' in iFileLines[i]:
			NAtoms = int(iFileLines[i].split('=')[1])
			CodeStatus('Number of atoms = '+str(NAtoms))

		## Next line
		i+=1

	## Find last geometry
	CodeStatus('Looking for last geometry', end=' ... ')
	i = len(iFileLines)-1
	while i < len(iFileLines) and i > -1:
		if 'ATOMIC_POSITIONS' in iFileLines[i]:
			print('found it!')
			break

		i-=1

	## Retrieve coordinates
	for j in range(NAtoms):
		i+=1
		Atomtype = iFileLines[i].split()[0]
		AtomCoord = [float(k) for k in iFileLines[i].split()[1:]]
		# Add New Atom type to registry
		if not Atomtype in AtomDict: AtomDict[Atomtype] = []
		# Add Atom to registry
		AtomDict[Atomtype].append(AtomCoord)






















#### Writting
CodeStatus('Creating POSCAR_'+iFileName.split('.')[0]+' file ')
with open('POSCAR_'+iFileName.split('.')[0], 'w') as f:
	CodeStatus('Writting coordinates', end=' ... ')
	# Tittle
	f.write('Translated from QuantumEspresso : '+iFileName)
	# Factor
	f.write('\n   1.00000000000000     ')
	# Cell
	for i in CellVectors:
		f.write('\n ')
		for j in i:
			f.write(FixStrLead(FixNum(j,16), 22))
	# Atom types
	f.write('\n')
	for i in AtomDict:
		f.write(FixStrLead(i,4))
	# Atom type amounts
	f.write('\n')
	for i in AtomDict:
		f.write(FixStrLead(str(len(AtomDict[i])),4))
	# Cell control
	f.write('\nSelective dynamics')
	f.write('\nCartesian')
	# Atom possitions
	for i in AtomDict:
		for j in AtomDict[i]:
			f.write('\n')
			for k in j:
				f.write(FixStrLead(FixNum(k,16),20))
			f.write('   F   F   F')
	print('Ok')

#### Writting POTCAR
CodeStatus('Writting dummy POTCAR file just for vmd', end=' ... ')
with open('POTCAR', 'w') as f:
	for iAt in AtomDict:
		f.write('  PAW_PBE '+iAt+' 01Feb1994'+' '*20+'\n')
		f.write(' End of Dataset\n')
print('Ok')