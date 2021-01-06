from PyQt5 import QtCore
from baseClasses import Student, Assignment, Program
from itemClasses import RootTreeItem, StudentTreeItem, AssignmentTreeItem, ProgramTreeItem
from os import scandir, path
from assignmentChecker import checkAssignment
import logging
from datetime import datetime
from PyQt5.QtCore import  QSettings
from commonElements import *

class StudentTreeModel(QtCore.QAbstractItemModel):
    """
    This model is used to display student information in a tree view
    """
    
    def __init__(self, startingStudentList, rootFolderPath, assignmentManager, restoreList = [],  startingParent = None):
        
        # initialize base class
        super(StudentTreeModel, self).__init__(startingParent)
        self.todaysDateTime = datetime.now().ctime().replace(" ", "_")
        self.appSettings = QSettings()
        if self.appSettings.contains('generateGradesAtStartup'):
            self.generateGradesOnStartup = self.appSettings.value('generateGradesAtStartup', type=bool)
        else:
            self.generateGradesOnStartup = False
        if self.appSettings.contains('generateStudentGradeFile'):
            self.generateStudentGradeFile = self.appSettings.value('generateStudentGradeFile', type=bool)
        else:
            self.generateStudentGradeFile = True
        if self.appSettings.contains('generateExcelFile'):
            self.generateExcelFile = self.appSettings.value('generateExcelFile', type=bool)
        else:
            self.generateExcelFile = True

        if len(restoreList) == 0:
            # create some data members, these will be set from the outside and trigger a model change
            self.students = self.createStudents(startingStudentList, rootFolderPath, assignmentManager)
        else:
            self.students = []
            for student in restoreList:
                self.addStudent(student)
        # set the root item to add other items to
        self.rootItem = RootTreeItem()
        self.setupModelData()

    def createStudents(self, startingStudentList, rootFolderPath, assignmentManager):
        """
        @return: Create the list of students from the list of students. If asked to generate grades on startup, call the
        checkAssignment and judge the run to the assignment definition in the assignment Manager.
        """
        self.logger = logging.getLogger("Fireheart.python.grader")
        students = []
        assignmentsNameList = assignmentManager.getAssignmentNames()                # Get the names of all of the assigned assignments.
        for studentName in startingStudentList:
            currentStudentRecord = Student(studentName, rootFolderPath)
            currentStudentsAssignments = []
            for directoryItem in scandir(path.join(rootFolderPath, studentName)):   # Scan the student's folder & collect all the
                if directoryItem.is_dir():                                          # potential assignments in there.
                    currentStudentsAssignments.append(directoryItem.name)
            # totalGrade = 0
            for assignmentName in assignmentsNameList:                              # Create an Assignment object for each assigned assignment.
                # resultsString = ""
                assignment = Assignment(assignmentName)
                assignmentProgramFilenameList = assignmentManager.getAssignmentProgramFilenamesList(assignmentName)
                if len(currentStudentsAssignments) > 0:
                    if assignmentName in currentStudentsAssignments:                # match up assigned assignments with found assignments.
                        assignment.clearMissing()                                   # Found the corresponding folder in the student's directory.
                    currentStudentsProgramFilenames = []                            # Now, get the names of the student's submitted program files.
                    basePathForAssignment = path.join(rootFolderPath, studentName, assignmentName)
                    if path.exists(basePathForAssignment):
                        for directoryContentItem in scandir(basePathForAssignment):
                            if not directoryContentItem.is_dir():
                                if directoryContentItem.name.endswith(".py") or directoryContentItem.name.endswith(".pyw"):  # Only Python files
                                    currentStudentsProgramFilenames.append(directoryContentItem.name)
                    # assignmentGrade = 0
                    for programFilename in assignmentProgramFilenameList:                   # Create a program object for each assigned program.
                        currentProgram = Program(programFilename)
                        if programFilename in currentStudentsProgramFilenames:
                            currentProgram.clearMissing()
                            currentProgram.setGrade(0)
                            # if self.generateGradesOnStartup:
                            #     assignmentGrade, errorString = checkAssignment(basePathForAssignment, assignmentManager.getAssignmentDefinition(assignmentName, programFilename), assignmentManager.getAssignmentTimeout(assignmentName))
                            #     self.logger.info("Result: %s: %s: %s: %s" % (studentName, assignmentName, programFilename, assignmentGrade))
                            # currentStudent.addAssignment(
                            #     (assignmentItem.name, assignmentGradeNames[assignmentGrade]))
                            #     resultsString += assignmentName + '\tGrade: ' + assignmentGradeNames[assignmentGrade] + '\n'
                            #     assignmentGrade += assignmentGrade
                            #     currentProgram.setGrade(assignmentGrade)
                                # currentProgram.setLastUpdateDate(self.todaysDateTime)
                                # if assignmentGrade < 2:
                                #     currentProgram.setErrors(errorString)
                        assignment.addProgram(currentProgram)
                # assignmentGrade /= len(assignmentProgramFilenameList)
                # assignment.setGrade(assignmentGrade)
                assignment.setGrade(0)
                # resultsString += "Assignment Grade: " + "%3.1f" % (assignmentGrade * 100) + '%\n'
                # if self.generateStudentGradeFile == True:
                #     if path.exists(path.join(basePathForAssignment, studentGradeFilename)):
                #         with open(path.join(basePathForAssignment, studentGradeFilename), 'w') as resultsFileHandle:
                #             resultsFileHandle.write(resultsString)
                # totalGrade += assignmentGrade
                currentStudentRecord.addAssignment(assignment)
            # totalGrade /= len(startingStudentList)
            # currentStudentRecord.setGrade(totalGrade)
            currentStudentRecord.setGrade(0)
            students.append(currentStudentRecord)
        return students

    def addStudent(self, studentRecord):
        self.students.append(studentRecord)

    def setupModelData(self):
        """ Creates items for the model the view can work with
        These are created out of the students held within the model
        """
        
        for student in self.students:
            
            # Create a student tree item
            studentItem = StudentTreeItem(self.rootItem, student)
            
            # for all the assignments attached to the student create an assignment
            for assignment in student.assignments:
                
                assignmentItem = AssignmentTreeItem(studentItem, assignment)
                
                for program in assignment.programs:
                    
                    # create the program item
                    programItem = ProgramTreeItem(assignmentItem, program)
                    
                    # add the program item to the assignment
                    assignmentItem.addChild(programItem)
                    
                # add the assignment item to the student
                studentItem.addChild(assignmentItem)
                
            # add the student to the root
            self.rootItem.addChild(studentItem)
                
                
                
    def index(self, row, column, parentIndex):
        """
        The index is used to access data by the view
        This method overrides the base implementation, needs to be overridden
        @param row: The row to create the index for
        @param column: Not really relevant, the tree item handles this
        @param parent: The parent this index should be created under 
        """
        
        # if the index does not exist, return a default index
        if not self.hasIndex(row, column, parentIndex):
            return QtCore.QModelIndex()
        
        # make sure the parent exists, if not assume it's the root
        parent_item = None
        if not parentIndex.isValid():
            parent_item = self.rootItem
        else:
            parent_item = parentIndex.internalPointer()
            
        # get the child from that parent and create an index for it
        childItem = parent_item.getChild(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()
        
        
        
    def parent(self, childIndex):
        """
        creates an index for a parent based on a child index, and binds the data
        used by the view to get a parent (from a child)
        @param childIndex: the index of the child to get the parent from
        """
        
        if not childIndex.isValid():
            return QtCore.QModelIndex()
        
        child_item = childIndex.internalPointer()
        if not child_item:
            return QtCore.QModelIndex()
        
        parent_item = child_item.getParent()
        
        if parent_item == self.rootItem:
            return QtCore.QModelIndex()
        
        return self.createIndex(parent_item.row(), 0, parent_item)
    
    
    
    def rowCount(self, parentIndex):
        """
        Returns the amount of rows a parent has
        This comes down to the amount of children associated with the parent
        @param parentIndex: the index of the parent
        """
        
        if parentIndex.column() > 0:
            return 0
        
        item = None
        if not parentIndex.isValid():
            item = self.rootItem
        else:
            item = parentIndex.internalPointer()
            
        return item.getChildCount()
    
    
    
    def columnCount(self, parentIndex):
        """
        Amount of columns associated with the parent index
        @param parentIndex: the parent index object
        """
        
        if not parentIndex.isValid():
            return self.rootItem.columnCount()
        
        return parentIndex.internalPointer().columnCount()
    
    
    
    def data(self, index, role):
        """
        The view calls this to extract data for the row and column associated with the parent object
        @param parentindex: the parentindex to extract the data from
        @param role: the data accessing role the view requests from the model
        """
        
        if not index.isValid():
            return QtCore.QVariant()
        
        # get the item out of the index
        parent_item = index.internalPointer()
        
        # Return the data associated with the column
        if role == QtCore.Qt.DisplayRole:
            return parent_item.data(index.column())
        if role == QtCore.Qt.SizeHintRole:
            return QtCore.QSize(50,50)
        
        # Otherwise return default
        return QtCore.QVariant()
    
    
    
    def headerData(self, column, orientation, role):
        if (orientation == QtCore.Qt.Horizontal and
        role == QtCore.Qt.DisplayRole):
            try:
                return self.rootItem.data(column)
            except IndexError:
                pass

        return QtCore.QVariant()