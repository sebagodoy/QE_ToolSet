#! /usr/bin/env python3

################################################################
#
#	QE.Geom_to_POSCAR.py
#
#	Function: 	reads geometries from QuantumEspresso output files
#				and produces XDATCAR VASP-type files that can be
#				easyly read with codes such as vmd.
#				Reads and writes, plots and saves list of energies
#				if user decides to do so.
#
#	Version:	1.0 - 25/10/2021
#
#	Comments:	Works for .out files
#				and extract from .out in process.
#	To do:		Check geometry from output and all factors
# 				Improve plot window to show.
#
#	Packages:	matplotlib.pyplot (if user requieres plotting)
#
#	Made by Sebastian Godoy
#	GitHub repository: https://github.com/sebagodoy/QE_ToolSet
#	Other Contributors:
#
#
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
		quit('\n'+' '*4+'¡'*8+'It\'s an input file. It should not contain a geometry sequence')

	if 'This program is part of the open-source Quantum ESPRESSO suite' in iFile:
		print('Ok')
except:
	CodeError('What a weird file, u sure is the right one?')




# Getting Data: base
LatParam = 1.0
NAtoms = 0
CellVectors = []
AtomDict = {}
E0dict = {}




# Searching cell data in file
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



## Find First geometry
CodeStatus('Looking for initial geometry', end=' ... ')
i = 0
while i < len(iFileLines) and i > -1:
	if 'ATOMIC_POSITIONS' in iFileLines[i]:
		print('found it!')
		break
	i+=1

## Retrieve initial coordinates
CodeStatus('Getting Initial coordinates', end=' ... ')
ConfigNumber=1
for j in range(NAtoms):
	i+=1
	Atomtype = iFileLines[i].split()[0]
	AtomCoord = [float(k) for k in iFileLines[i].split()[1:]]
	# Add New Atom type to registry
	if not Atomtype in AtomDict: AtomDict[Atomtype] = []
	# Add Atom to registry
	AtomDict[Atomtype].append(AtomCoord)
print('Ok')






AtomDict_Bkp = AtomDict


#### Writting initial block
CodeStatus('Creating XDATCAR5_'+iFileName.split('.')[0]+' file ')
with open('relaxMovie_XDATCAR5_'+iFileName.split('.')[0], 'w') as f:
	CodeStatus('Writting initial coordinates ', end=' ... ')
	# Tittle
	f.write('Translated from QuantumEspresso : '+iFileName)
	# Factor
	f.write('\n   1.00000000000000     ')
	# Cell
	for k in CellVectors:
		f.write('\n ')
		for j in k:
			f.write(FixStrLead(FixNum(j,16), 22))
	# Atom types
	f.write('\n')
	for k in AtomDict:
		f.write(FixStrLead(k,4))
	# Atom type amounts
	f.write('\n')
	for k in AtomDict:
		f.write(FixStrLead(str(len(AtomDict[k])),4))
	# Config number
	f.write('\nDirect configuration=     1')

	# Atom possitions
	for m in AtomDict:
		for j in AtomDict[m]:
			f.write('\n')
			for k in range(len(j)):
				f.write(FixStrLead(FixNum(j[k]/CellVectors[k][k],16),20))
			# f.write('   F   F   F')
	print('Ok')





try:
	#### Getting new geometries
	CodeStatus('Looking for next coordinates')
	CodeStatus('Coodinates found : ', end='')
	NCoordReport=20

	while i < len(iFileLines):
		#debug
		# print('Look for next Geom: current line='+str(i)+' of '+str(len(iFileLines))+' for max='+str(len(iFileLines)-1))

		# Identify start
		while i < len(iFileLines):
			# debug:
			# print('Looking Geom Start, i='+str(i)+':'+iFileLines[i])
			## New Geom energy
			if '!    total energy              =' in iFileLines[i]:
				E0dict[ConfigNumber+1] = float(iFileLines[i].split()[4])
			## New Geometry
			if 'ATOMIC_POSITIONS' in iFileLines[i]:
				break
			i += 1

		# Get out if document finished
		if i == len(iFileLines):
			print('(end of document)='+str(ConfigNumber))
			break

		# Prepare to get coordinates
		ConfigNumber += 1
		NCoordReport += 1
		AtomDict = {}
		#debug
		# CodeStatus('Found geometry '+str(ConfigNumber))

		# report found
		if NCoordReport <45:
			print('.', end='')
		else:
			print('\n'+' '*8+'.', end='')
			NCoordReport=0


		# Get coordinates
		try:
			for j in range(NAtoms):
				i += 1
				#debug
				# print(' '*8+'> Atom:'+iFileLines[i])
				Atomtype = iFileLines[i].split()[0]
				AtomCoord = [float(k) for k in iFileLines[i].split()[1:]]
				# Add New Atom type to registry
				if not Atomtype in AtomDict: AtomDict[Atomtype] = []
				# Add Atom to registry
				AtomDict[Atomtype].append(AtomCoord)
		except:
			print('\n'+'¡!'*60)
			print(' '*4+'Something went wrong with last geometry, Geom N='+str(ConfigNumber))

		# Writte that down
		with open('relaxMovie_XDATCAR5_' + iFileName.split('.')[0], 'a') as f:
			f.write('\nDirect configuration=     ' + str(ConfigNumber))
			for m in AtomDict:
				for j in AtomDict[m]:
					f.write('\n')
					for k in range(len(j)):
						f.write(FixStrLead(FixNum(j[k] / CellVectors[k][k], 16), 20))

except:
	print('\n' + '¡!' * 60)
	print('Something went wrong, better check manually. Even though, let\'s continue')



#### Ending Configuration list
CodeStatus('Ending XDATCAR5 file')
with open('relaxMovie_XDATCAR5_'+iFileName.split('.')[0], 'a') as f:
	f.write('\nDirect configuration=     '+str(ConfigNumber+1))

#### Writte energies
WE0_input = input(' '*4+'Writte energies to *.E0 file (def=y / n) ? ')
if WE0_input == '': WE0_input='y'
if WE0_input == 'y':
	with open(iFileName.split('.')[0]+'.E0.log', 'w') as f:
		f.write(' Electronic energies from '+iFileName+', QuantumEspresso relaxation Job\n')
		f.write('Values extracted when creating the '+'relaxMovie_XDATCAR5_' + iFileName.split('.')[0]+' file\n')
		for iE0 in E0dict:
			f.write(' Geom = '+str(iE0)+' , E0 = '+str(E0dict[iE0])+'\n')
		f.write(' ---- End of file ---- ')

#### Show energies
ShE0_input = input(' '*4+'Wanna see those energies (y : plot/ s : save / def=ys : both / n : no) ? ')
if ShE0_input == '': ShE0_input = 'ys'

if 'y' in ShE0_input or 's' in ShE0_input:
	# Creando
	import matplotlib.pyplot as plt
	fig, ax = plt.subplots()
	ax.set_title('Relaxation in '+iFileName, y=.95, x=.98, ha='right', va='top')
	ax.plot([k for k in E0dict], [E0dict[k] for k in E0dict], '+')
	ax.grid(which='major', axis='both')
	ax.set(xlabel='Iteration', ylabel='Electronic energy /  Ry')

	# Extra axis
	axkJ = ax.twinx()
	UnitTransform = (2.1798723611035e-21)*(6.0221409e23)

	axkJ.set_ylabel('Electronic energy / kJ/mol')
	yMin, ymax = ax.get_ylim()
	tickList_Ry = ax.get_yticks()[1:-1]
	print('ymax:'+str(ymax))
	print('ticklist:'+str(tickList_Ry))
	axkJ.set_ylim(yMin*UnitTransform, ymax*UnitTransform)

	# Fix axis
	OffsetkJ  = ymax
	axkJ.ticklabel_format(style='plain', useOffset=True)
	tickList_kJmol = [k * UnitTransform for k in ax.get_yticks()[1:-1]]
	axkJ.set_yticks(tickList_kJmol)

	# grabando?
	if 's' in ShE0_input:
		plt.savefig(iFileName.split('.')[0]+'.png', bbox_inches='tight')

	# mostrando?
	if 'y' in ShE0_input:
		plt.show()



#### Writting POTCAR
CodeStatus('Writting dummy POTCAR file just for vmd', end=' ... ')
with open('POTCAR', 'w') as f:
	for iAt in AtomDict:
		f.write('  PAW_PBE '+iAt+' 01Feb1994'+' '*20+'\n')
		f.write(' End of Dataset\n')
print('Ok')
CodeStatus('All done, cheers!')