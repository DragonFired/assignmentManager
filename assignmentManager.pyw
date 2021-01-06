#!/usr/bin/env python

from sys import argv, exit
from os import scandir, path, walk, stat
from subprocess import check_output, STDOUT
from logging import basicConfig, getLogger, INFO
from pickle import dump, load
from datetime import date
from os.path import expanduser
from PyQt5 import QtGui, uic
from PyQt5.QtCore import pyqtSlot, QSettings, Qt, QCoreApplication, QTimer, QDir
from PyQt5.QtWidgets import QMainWindow, QApplication, QDialog, QMessageBox, QFileSystemModel
# from studentModel import StudentTreeModel

import assignmentManagerResources_rc
from defaults import *


class assignmentManager(QMainWindow):
    """ This program 'looks' at files in the given directory for labels.
    It generates a list of files without a RED, GREEN or YELLOW label. """

    def __init__(self, parent=None):
        """ Build a GUI  main window for assignmentManager."""

        super().__init__(parent)
        self.logger = getLogger("Fireheart.assignmentManager")
        self.appSettings = QSettings()
        self.quitCounter = 0;       # used in a workaround for a QT5 bug.

        self.pickleFilename = pickleFilenameDefault
        self.restoreSettings()
        try:
            self.pickleFilename = self.restoreApp()
        except FileNotFoundError:
            self.restartApp()

        uic.loadUi("assignmentManagerMainWindow.ui", self)

        self.monthNames = {"Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
                            "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12}
        self.home = expanduser("~")
        # self.startingFoldername = startingFoldernameDefault
        # self.startingFoldername = path.join(self.home, self.startingFoldername)
        self.gradeDataFilename = gradeDataFilenameDefault
        self.gradeConversion = {"Red": 0, "Yellow": 75, "Green": 100, "Purple": 120}
        self.fileEndingsByLanguage = {"Python": (".py",), "C++": (".cpp", ".h",)}

        # if not path.exists(fullAssignmentsFilename):
        #     self.alerts = "Could not find Assignments File: %s" % fullAssignmentsFilename
        self.alerts = ""

        self.preferencesSelectButton.clicked.connect(self.preferencesSelectButtonClickedHandler)
        self.refreshGradesButton.clicked.connect(self.refreshGradesButtonClickedHandler)
        self.rootFolderSelectButton.clicked.connect(self.rootFolderSelectButtonClickedHandler)
        self.calendarButton.clicked.connect(self.calendarButtonClickedHandler)
        self.currentFilePathUI.clicked.connect(self.rootFolderSelectButtonClickedHandler)
        self.startOfTermUI.clicked.connect(self.calendarButtonClickedHandler)
        self.trashStudentReportsButton.clicked.connect(self.trashStudentReportsButtonClickedHandler)

    def __str__(self):
        """String representation for assignmentManager.
        """

        return "Gettin' started with Qt!!"

    # def buildStudentsModel(self, startingFolderName, assignmentsManager, restoredStudentsList):
    #     if len(restoredStudentsList) == 0:
    #
    #         studentNameList = []                                # List of all students to be graded. Obtained from folder names in root directory.
    #         for directoryItem in scandir(startingFolderName):
    #             if directoryItem.is_dir():
    #                 studentNameList.append(directoryItem.name)
    #         self.logger.info(studentNameList)
    #         self.logger.info("###################")
    #
    #         studentModel = StudentTreeModel(studentNameList, startingFolderName, assignmentsManager)
    #     else:                                                   # Found a restorable previous version of the grading object.
    #         studentNameList = []                                # List of all students to be graded. Obtained from restoredStudentsList.
    #         for student in restoredStudentsList:
    #             studentNameList.append(student.getName())
    #         studentModel = StudentTreeModel(studentNameList, startingFolderName, assignmentsManager, restoreList = restoredStudentsList)
    #
    #     self.studentsTreeView.setModel(studentModel)
    #     return studentModel

    def setStartingFolderName(self, newFolderName):
        self.startingFoldername = newFolderName
        self.appSettings.setValue('startingFolderName', self.startingFoldername)
        # self.studentModel = self.buildStudentsModel(self.startingFolderName, self.currentAssignmentsManager, [])

    def getStartingFolderName(self):
        return self.startingFoldername

    def setSemesterStartDate(self, newStartDate):
        self.semesterStartDate = newStartDate
        self.appSettings.setValue('semesterStartDate', self.semesterStartDate)

    def getSemesterStartDate(self):
        return self.semesterStartDate

    def updateUI(self):
        self.currentFilePathUI.setText(self.startingFoldername)
        self.startOfTermUI.setText(self.semesterStartDate.strftime("%b %d, %Y"))
        if self.alerts != '':
            self.statusBarTimer = QTimer()
            self.statusBarTimer.singleShot(6500, self.clearStatusBar)
        self.statusBar.showMessage(self.alerts)

    def clearStatusBar(self):
        print("Clearing the status bar")
        self.alerts = ""
        self.updateUI()

    def restartApp(self):
        if self.createLogFile:
            self.logger.debug("Restarting game")

    def saveApp(self):
        if self.createLogFile:
            self.logger.debug("Saving game")
        saveItems = (self.startingFoldername, self.semesterStartDate)
        if self.appSettings.contains('pickleFilename'):
            with open(path.join(path.dirname(path.realpath(__file__)),  self.appSettings.value('pickleFilename', type=str)), 'wb') as pickleFile:
                dump(saveItems, pickleFile)
        elif self.createLogFile:
            self.logger.critical("No pickle Filename")

    def restoreApp(self):
        if self.appSettings.contains('pickleFilename'):
            self.appSettings.value('pickleFilename', type=str)
            with open(path.join(path.dirname(path.realpath(__file__)),  self.appSettings.value('pickleFilename', type=str)), 'rb') as pickleFile:
                return load(pickleFile)
        else:
            self.logger.critical("No pickle Filename")

    def restoreSettings(self):
        if appSettings.contains('createLogFile'):
            self.createLogFile = appSettings.value('createLogFile')
        else:
            self.createLogFile = createLogFileDefault
            appSettings.setValue('createLogFile', self.createLogFile)

        if self.createLogFile:
            self.logger.debug("Starting restoreSettings")
        # Restore settings values, write defaults to any that don't already exist.

        if self.appSettings.contains('semesterStartDate'):
            self.semesterStartDate = self.appSettings.value('semesterStartDate', type=datetime)
        else:
            self.semesterStartDate = semesterStartDateDefault
            self.appSettings.setValue('semesterStartDate', self.semesterStartDate)

        if self.appSettings.contains('startingFoldername'):
            self.startingFoldername = self.appSettings.value('startingFoldername', type=str)
        else:
            self.startingFoldername = startingFoldernameDefault
            self.appSettings.setValue('startingFoldername', self.startingFoldername)

        if self.appSettings.contains('gradeDataFilename'):
            self.gradeDataFilename = self.appSettings.value('gradeDataFilename', type=str)
        else:
            self.gradeDataFilename = gradeDataFilenameDefault
            self.appSettings.setValue('gradeDataFilename', self.gradeDataFilename)

        if self.appSettings.contains('createLogFile'):
            self.createLogFile = self.appSettings.value('createLogFile')
        else:
            self.createLogFile = logFilenameDefault
            self.appSettings.setValue('createLogFile', self.createLogFile)

        if self.appSettings.contains('logFile'):
            self.logFilename = self.appSettings.value('logFile', type=str)
        else:
            self.logFilename = logFilenameDefault
            self.appSettings.setValue('logFile', self.logFilename)

        if self.appSettings.contains('pickleFilename'):
            self.pickleFilename = self.appSettings.value('pickleFilename', type=str)
        else:
            self.pickleFilename = pickleFilenameDefault
            self.appSettings.setValue('pickleFilename', self.pickleFilename)

        if self.appSettings.contains('languageChoice'):
            self.languageChoice = self.appSettings.value('languageChoice', type=str)
        else:
            self.languageChoice = languageChoiceDefault
            self.appSettings.setValue('languageChoice', self.languageChoice)

    def getLastRecordingDate(self, filename):
        try:
            with open(filename, 'r') as pastReportFile:
                logLine = pastReportFile.readline()
                dateString = logLine.split(': ')[-1].strip().replace("_", " ")
                lRWeekday, lRMonth, lRDay, lRTime, lRYear = dateString.split()
                lRHour, lRMinute, lRSecond = lRTime.split(':')
                previousDate = datetime(month=self.monthNames[lRMonth], day=int(lRDay), year=int(lRYear), hour=int(lRHour), minute=int(lRMinute), second=int(lRSecond))
        except FileNotFoundError:
            print(f"{filename} doesn't exist.")
            self.logger.error("Previous Grade Data File Not Found. First run?")
        except ValueError:
            previousDate = self.semesterStartDate
        return previousDate

    def getStudentList(self, folderName):
        try:
            namesList = []
            for directoryItem in scandir(folderName):
                if directoryItem.is_dir():
                    if not directoryItem.name.startswith('.'):
                        namesList.append(directoryItem.name)
            return namesList
        except FileNotFoundError:
            self.logger.info("Folder {0} doesn't exist".format(folderName))
            self.alerts = f"Folder {folderName} doesn't exist"

    def processStudentFiles(self, studentNamesList, previousUpdateTime):
        lastUpdated = previousUpdateTime.timestamp()
        masterList = ""
        emptyList = ""
        ungradedAssignmentCount = emptyAssignmentCount = 0

        currentDateTime = datetime.now().ctime().replace(" ", "_")
        masterList += "Recorded on: {0}\n".format(currentDateTime)

        for student in studentNamesList:
            studentName = student.split('-')[0]
            masterList += f"\n{studentName}\n"
            emptyList += f"\n{studentName}\n"
            for assignmentDirectory in scandir(path.join(self.startingFoldername, student)):
                assignmentsList = []
                if assignmentDirectory.is_dir():
                    noTagsFound = True
                    codeFilesFound = False
                    for rootPath, dirs, files in walk(path.join(self.startingFoldername, student, assignmentDirectory)):
                        for file in files:
                            # noFilesFound = False
                            fullFilePath = path.join(rootPath, file)
                            command = 'tag "' + fullFilePath + '"'
                            returnString = check_output(command, stderr=STDOUT, shell=True).decode(
                                "UTF8")
                            filename, fileExtension = path.splitext(fullFilePath)
                            if fileExtension in self.fileEndingsByLanguage[self.languageChoice]:  # File is a code file
                                codeFilesFound = True
                                fileStats = stat(fullFilePath)
                                lastModTime = fileStats.st_mtime
                                if returnString.count(
                                        '\t') == 0 or lastModTime > lastUpdated:  # It has NOT been tagged.
                                    fileName = returnString
                                    if self.languageChoice == "C++":
                                        projectFoldername = path.split(path.dirname(fileName))[-1]
                                        assignmentsList.append((path.basename(fileName), projectFoldername))
                                    else:
                                        assignmentsList.append((path.basename(fileName)))
                    if len(assignmentsList) > 0:
                        for item in assignmentsList:
                            fileContents = "Assignment {0}:\tFile: {1}".format(assignmentDirectory.name, item.strip())
                            masterList += fileContents + '\n'
                            ungradedAssignmentCount += 1
                    else:
                        emptyList += "Assignment {0}: Empty\n".format(assignmentDirectory.name)
                        emptyAssignmentCount += 1
        return emptyAssignmentCount, emptyList, masterList, ungradedAssignmentCount

    def createReportFile(self, reportFilename, masterList, emptyList):
        with open(reportFilename, 'w') as masterDataFile:
            masterDataFile.write(masterList)
            masterDataFile.write("\n\n*****************************************\n\nEmpty List:\n")
            masterDataFile.write(emptyList)

    def refreshGradesButtonClickedHandler(self):
        print("Inside pushButtonClickedHandler()\n")
        self.lastUpdatedDate = self.getLastRecordingDate(path.join(self.startingFoldername, self.gradeDataFilename))
        studentList = self.getStudentList(self.startingFoldername)
        studentList.sort()
        emptyAssignmentCount, emptyFolderList, allGradesList, ungradedAssignmentCount = self.processStudentFiles(studentList, self.lastUpdatedDate)
        self.createReportFile(path.join(self.startingFoldername, self.gradeDataFilename), allGradesList, emptyFolderList)
        print(f"{ungradedAssignmentCount} ungraded files, and \n{emptyAssignmentCount} empty assignments folders.")

        self.updateUI()

    @pyqtSlot()  # User is requesting a top level folder select.
    def rootFolderSelectButtonClickedHandler(self):
        folderDialog = FolderSelectDialog(self.getStartingFolderName())
        folderDialog.show()
        folderDialog.exec_()
        self.updateUI()

    @pyqtSlot()  # User is requesting a top level folder select.
    def calendarButtonClickedHandler(self):
        calendarDialog = StartOfTermSelectDialog(self.semesterStartDate)
        calendarDialog.show()
        calendarDialog.exec()
        self.updateUI()

    @pyqtSlot()  # User is requesting preferences editing dialog box.
    def preferencesSelectButtonClickedHandler(self):
        if self.createLogFile:
            self.logger.info("Setting preferences")
        preferencesDialog = PreferencesDialog()
        preferencesDialog.show()
        preferencesDialog.exec()
        self.restoreSettings()              # 'Restore' settings that were changed in the dialog window.
        self.updateUI()

    @pyqtSlot()  # User has requesting we remove all student report files.
    def trashStudentReportsButtonClickedHandler(self):
        for root, directories, files in walk(self.startingFoldername):
            for name in files:
                if name == studentGradeFilename:
                    remove(path.join(root, name))
                    # print('Removing file %s in directory %s' % (name, root))

    @pyqtSlot()				# Player asked to quit the game.
    def closeEvent(self, event):
        if self.createLogFile:
            self.logger.debug("Closing app event")
        if self.quitCounter == 0:
            self.quitCounter += 1
            quitMessage = "Are you sure you want to quit?"
            reply = QMessageBox.question(self, 'Message', quitMessage, QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                self.saveApp()
                event.accept()
            else:
                self.quitCounter = 0
                event.ignore()
            # return super().closeEvent(event)


class FolderSelectDialog(QDialog):
    def __init__(self, startingFolderName, parent = assignmentManager):
        super(FolderSelectDialog, self).__init__()
        uic.loadUi('rootSelectDialog.ui', self)
        fileModel = QFileSystemModel()
        fileModel.setFilter(QDir.Dirs | QDir.NoDot | QDir.NoDotDot)
        fileModel.setRootPath(startingFolderName)
        self.selectedPath = ""
        self.fileSelectTreeView.setModel(fileModel)
        self.fileSelectTreeView.resizeColumnToContents(0)

        self.fileSelectTreeView.doubleClicked.connect(self.fileDoubleClickedHandler)
        self.buttonBox.rejected.connect(self.cancelClickedHandler)
        self.buttonBox.accepted.connect(self.okayClickedHandler)
        self.fileSelectTreeView.clicked.connect(self.selectionChangedHandler)
        self.fileSelectTreeView.expanded.connect(self.itemExpandedHandler)

    # @pyqtSlot()
    def fileDoubleClickedHandler(self, signal):
        # print(signal)
        filePath = self.fileSelectTreeView.model().filePath(signal)
        if path.isdir(filePath):
            # print(filePath)
            assignmentManagerApp.setStartingFolderName(filePath)
            self.close()
        else:
            print("File selected, not directory")

    # @pyqtSlot()
    def okayClickedHandler(self):
        # print(self.selectedPath)
        if path.isdir(self.selectedPath):
            assignmentManagerApp.setStartingFolderName(self.selectedPath)
            self.close()
        else:
            print("File Selected on Okay")

    # @pyqtSlot(QItemSelection)
    def selectionChangedHandler(self, selected):
        self.fileSelectTreeView.resizeColumnToContents(0)
        # print(selected)
        if path.isdir(self.fileSelectTreeView.model().filePath(selected)):
            self.selectedPath = self.fileSelectTreeView.model().filePath(selected)
            # print(self.selectedPath)
        else:
            print("File Selected")

    # @pyqtSlot()
    def itemExpandedHandler(self, selected):
        self.fileSelectTreeView.resizeColumnToContents(0)

    # @pyqtSlot()
    def cancelClickedHandler(self):
        self.close()


class StartOfTermSelectDialog(QDialog):
    def __init__(self, currentStartDate, parent=assignmentManager):
        super(StartOfTermSelectDialog, self).__init__()
        uic.loadUi('dateSelectDialog.ui', self)
        self.selectedDate = currentStartDate

        self.buttonBox.rejected.connect(self.cancelClickedHandler)
        self.buttonBox.accepted.connect(self.okayClickedHandler)
        self.startOfTermSelect.clicked.connect(self.dateSelectionChangedHandler)

    # @pyqtSlot()
    def dateSelectionChangedHandler(self, signal):
        self.selectedDate = date(year=signal.year(), month=signal.month(), day=signal.day())

    # @pyqtSlot()
    def okayClickedHandler(self):
        assignmentManagerApp.setSemesterStartDate(self.selectedDate)
        self.close()

    # @pyqtSlot()
    def cancelClickedHandler(self):
        self.close()


class PreferencesDialog(QDialog):
    def __init__(self, parent=assignmentManager):
        super(PreferencesDialog, self).__init__()

        uic.loadUi('preferencesDialog.ui', self)
        self.logger = getLogger("Fireheart.craps")

        self.appSettings = QSettings()
        if self.appSettings.contains('languageChoice'):
            self.languageChoice = self.appSettings.value('languageChoice', type=str)
        else:
            self.languageChoice = languageChoiceDefault
            self.appSettings.setValue('languageChoice', self.languageChoice)

        if self.appSettings.contains('gradeDataFilename'):
            self.gradeDataFilename = self.appSettings.value('gradeDataFilename', type=str)
        else:
            self.gradeDataFilename = gradeDataFilenameDefault
            self.appSettings.setValue('gradeDataFilename', self.gradeDataFilename)

        if self.appSettings.contains('startingFoldername'):
            self.startingFoldername = self.appSettings.value('startingFoldername', type=str)
        else:
            self.startingFoldername = startingFoldernameDefault
            self.appSettings.setValue('startingFoldername', self.startingFoldername)

        if self.appSettings.contains('logFilename'):
            self.logFilename = self.appSettings.value('logFilename', type=str)
        else:
            self.logFilename = logFilenameDefault
            self.appSettings.setValue('logFilename', self.logFilename)

        if self.appSettings.contains('createLogFile'):
            self.createLogFile = self.appSettings.value('createLogFile')
        else:
            self.createLogFile = logFilenameDefault
            self.appSettings.setValue('createLogFile', self.createLogFile )

        self.buttonBox.rejected.connect(self.cancelClickedHandler)
        self.buttonBox.accepted.connect(self.okayClickedHandler)
        self.languageChoiceUI.currentIndexChanged.connect(self.languageChoiceUIChanged)
        self.dataFilenameUI.textChanged.connect(self.dataFilenameUIChanged)
        self.startingFoldernameUI.textChanged.connect(self.startingFoldernameUIChanged)
        self.createLogfileCheckBoxUI.stateChanged.connect(self.createLogFileChanged)
        self.languageChoice = self.languageChoiceUI.itemText(self.languageChoiceUI.currentIndex())

        self.updateUI()

    # @pyqtSlot()
    def languageChoiceUIChanged(self):
        self.languageChoiceUI = self.languageChoiceUI.itemText(self.languageChoiceUI.currentIndex())

    # @pyqtSlot()
    def dataFilenameUIChanged(self):
        self.dataFilenameUI = self.dataFilenameUI.text()

    # @pyqtSlot()
    def startingFoldernameUIChanged(self):
        self.startingFoldernameUI = self.startingFoldernameUI.text()

    # @pyqtSlot()
    def createLogFileChanged(self):
        self.createLogFile = self.createLogfileCheckBoxUI.isChecked()

    def updateUI(self):
        self.languageChoice = self.languageChoiceUI.itemText(self.languageChoiceUI.currentIndex())
        self.dataFilenameUI.setText(self.gradeDataFilename)
        self.startingFoldernameUI.setText(self.startingFoldername)
        if self.createLogFile:
            self.createLogfileCheckBoxUI.setCheckState(Qt.Checked)
        else:
            self.createLogfileCheckBoxUI.setCheckState(Qt.Unchecked)

    # @pyqtSlot()
    def okayClickedHandler(self):
        # write out all settings
        preferencesGroup = (('firstVariable', self.languageChoiceUI),
                            ('secondVariable', self.dataFilenameUI),
                            ('thirdVariable', self.startingFoldernameUI),
                            ('logFile', self.logFilename),
                            ('createLogFile', self.createLogFile),
                            )
        # Write settings values.
        for setting, variableName in preferencesGroup:
            # if self.appSettings.contains(setting):
            self.appSettings.setValue(setting, variableName)

        self.close()

    # @pyqtSlot()
    def cancelClickedHandler(self):
        self.close()


if __name__ == "__main__":
    QCoreApplication.setOrganizationName("Fireheart Software");
    QCoreApplication.setOrganizationDomain("fireheartsoftware.com");
    QCoreApplication.setApplicationName("assignmentManager");
    appSettings = QSettings()
    if appSettings.contains('createLogFile'):
        createLogFile = appSettings.value('createLogFile')
    else:
        createLogFile = createLogFileDefault
        appSettings.setValue('createLogFile', createLogFile)

    if createLogFile:
        startingFolderName = path.dirname(path.realpath(__file__))
        if appSettings.contains('logFile'):
            logFilename = appSettings.value('logFile', type=str)
        else:
            logFilename = logFilenameDefault
            appSettings.setValue('logFile', logFilename)
        basicConfig(filename=path.join(startingFolderName, logFilename), level=INFO,
                    format='%(asctime)s %(name)-8s %(levelname)-8s %(message)s')
    app = QApplication(argv)
    assignmentManagerApp = assignmentManager()
    assignmentManagerApp.updateUI()
    assignmentManagerApp.show()
    exit(app.exec_())
