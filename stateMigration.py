#!/usr/bin/python

'''
File: stateMigration.py
Authors: Heriberto Nieto, TACC Visualization Laboratory, http://www.tacc.utexas.edu/resources/visualization
Description: parses DisplayCluster state XML, copies media referenced in state file into destination folder, creates new state file using copied files
'''

#!/usr/bin/python

import wx
import os
import re
import shutil
import xml.etree.ElementTree as ET

mediaFileList = []
wildcard = "DisplayCluster State File (*.dcx)|*.dcx;" \
         "All files (*.*)|*.*"

class GUI(wx.Frame):
    
    '''
    LAYOUT
    '''

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="DisplayCluster State Migration Tool", size=(500, 200), style=wx.DEFAULT_FRAME_STYLE)
        
        self.panel = wx.Panel(self)
        self.gridSizer = wx.GridBagSizer(5, 5)

        # text boxes
        self.oldStateLabel = wx.StaticText(self.panel, label="Old State File")
        self.gridSizer.Add(self.oldStateLabel, pos=(1, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.oldStateTextBox = wx.TextCtrl(self.panel, value="/path/to/old/state/file.dcx")
        self.gridSizer.Add(self.oldStateTextBox, pos=(1, 1), span=(1, 3), flag=wx.TOP|wx.EXPAND, border=5)
        
        self.oldStateButton = wx.Button(self.panel, label="Browse...")
        self.gridSizer.Add(self.oldStateButton, pos=(1, 4), flag=wx.TOP|wx.RIGHT, border=5)

        self.newStateLabel = wx.StaticText(self.panel, label="New State File")
        self.gridSizer.Add(self.newStateLabel, pos=(2, 0), flag=wx.LEFT|wx.TOP, border=10)

        self.newStateTextBox = wx.TextCtrl(self.panel, value="sampleState.dcx")
        self.gridSizer.Add(self.newStateTextBox, pos=(2, 1), span=(1, 3), flag=wx.TOP|wx.EXPAND, border=5)

        self.outputDirLabel = wx.StaticText(self.panel, label="Output Directory")
        self.gridSizer.Add(self.outputDirLabel, pos=(3, 0), flag=wx.TOP|wx.LEFT, border=10)
        
        self.outputDirTextBox = wx.TextCtrl(self.panel, value="/path/to/new/state/")
        self.gridSizer.Add(self.outputDirTextBox, pos=(3, 1), span=(1, 3), flag=wx.TOP|wx.EXPAND, border=5)
        
        self.outputDirButton = wx.Button(self.panel, label="Browse...")
        self.gridSizer.Add(self.outputDirButton, pos=(3, 4), flag=wx.TOP|wx.RIGHT, border=5)

        self.migrateButton = wx.Button(self.panel, label="Migrate")
        self.gridSizer.Add(self.migrateButton, pos=(5, 0), flag=wx.LEFT, border=10)

        self.gridSizer.AddGrowableCol(2)        
        self.panel.SetSizer(self.gridSizer)

        # Bind event handlers to all controls that have one.
        self.oldStateButton.Bind(wx.EVT_BUTTON, self.getOldState)
        self.outputDirButton.Bind(wx.EVT_BUTTON, self.getOutputDir)
        self.migrateButton.Bind(wx.EVT_BUTTON, self.migrateState)
        
    '''
    EVENT HANDLERS
    '''
        
    def getOldState(self, event):
        dlg = wx.FileDialog(self, message="Choose state (*.dcx) file", wildcard=wildcard, style=wx.FD_OPEN)
        if dlg.ShowModal() == wx.ID_OK:
            selectedPath = dlg.GetPath()
            self.oldStateTextBox.SetValue(selectedPath)
        dlg.Destroy()
        
    def getOutputDir(self, event):
        dlg = wx.DirDialog(self, "", style=wx.DD_DEFAULT_STYLE | wx.DD_NEW_DIR_BUTTON)
        if dlg.ShowModal() == wx.ID_OK:
            selectedPath = dlg.GetPath()
            self.outputDirTextBox.SetValue(selectedPath)
        dlg.Destroy()
        
    def migrateState(self, event):
        if self.validateOldState() and self.validateNewState() and self.validateOutputDir():
            self.parseDCX()
            self.copyFiles()
            self.updateNewDCX()
            self.exitApp()

    def exitApp(self):
        dlg = wx.MessageDialog(self, "State Migration Complete", "Exit", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()
        self.Close(True)

    '''
    MIGRATION
    '''

        def parseDCX(self):
        print "Parsing old state file XML."
                tree = ET.parse(self.oldStateTextBox.GetValue())
                root = tree.getroot()
                   
        print "Media files from old state file:"
                for uri in root.getiterator('URI'):
            print uri.text
                        mediaFileList.append(uri.text)

    def copyFiles(self):
        print "\nPopulating output directory."
        # copy state file
        oldStatePath = self.oldStateTextBox.GetValue()
        newStatePath = os.path.join(self.outputDirTextBox.GetValue(), self.newStateTextBox.GetValue())
        shutil.copyfile(oldStatePath, newStatePath)
        print "New state file copied."         
        
        # create content directory
        contentDir = os.path.join(self.outputDirTextBox.GetValue(), "Content")
        os.makedirs(contentDir)

        # copy media
        print "Copying media ..."
        for src in mediaFileList:
            filename, extension = os.path.splitext(os.path.basename(src))
            
            # pyramid images must have their corresponding folder copied too
            if extension == ".pyr":
                # if the pyr file already exists in destination folder, then it has
                # been copied in an earlier iteration of the for loop and we can skip it
                if ( not os.path.isfile(os.path.join(contentDir, os.path.basename(src))) ):
                    # get old pyramid directory from pyr file
                    pyr = open(src, 'r')
                    oldPyramidFolder = pyr.readline().partition(' ')[0].replace('"', '').strip()

                    # copy pyramid folder w/ shutil.copytree(src, dst)
                    newPyramidFolder = os.path.join(contentDir, filename + ".pyramid")
                    shutil.copytree(oldPyramidFolder, newPyramidFolder, symlinks=False, ignore=None)
                    print newPyramidFolder

                    # copy pyr file
                    dest = os.path.join(contentDir, "copy-" + os.path.basename(src))
                    print dest
                    shutil.copyfile(src, dest)

                    # fix new pyr file to link to new pyramid folder path
                    with open(os.path.join(contentDir, os.path.basename(src)), "w") as newPyr:
                        with open(os.path.join(contentDir, "copy-" + os.path.basename(src)), "r") as copyPyr:
                            for line in copyPyr:
                                newPyr.write(line.replace(oldPyramidFolder, newPyramidFolder))

                    # remove copy of pyr file
                    os.remove(os.path.join(contentDir, "copy-" + os.path.basename(src)))
            
            # all other media files require only a single copy command
            else:    
                dest = os.path.join(contentDir, os.path.basename(src))
                print dest    
                shutil.copyfile(src, dest)
                
        print "Media copy complete."

    def updateNewDCX(self):
        print "\nUpdating new state file with output directory media."    
        newStatePath = os.path.join(self.outputDirTextBox.GetValue(), self.newStateTextBox.GetValue())
                tree = ET.parse(newStatePath)
                root = tree.getroot()
                
                for uri in root.getiterator('URI'):
            newURI = os.path.join(self.outputDirTextBox.GetValue(), "Content", os.path.basename(uri.text))
            uri.text = newURI
            print newURI

        # save modified dcx
        tree.write(newStatePath)

    '''
    VALIDATORS
    '''
    
    def validateOldState(self):
        # check if textbox is empty
        if len(self.oldStateTextBox.GetValue()) == 0:
            wx.MessageBox("Please select a .dcx file.", "Error")
            self.oldStateTextBox.SetBackgroundColour("pink")
            self.oldStateTextBox.SetFocus()
            self.oldStateTextBox.Refresh()
            return False
        else:
            self.oldStateTextBox.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            self.oldStateTextBox.Refresh()

            # check if directory exists
            if not os.path.exists(self.oldStateTextBox.GetValue()):
                wx.MessageBox("The dcx file does not exist.\nVerify your spelling and format or use the directory dialog.", "Error")
                self.oldStateTextBox.SetBackgroundColour("pink")
                self.oldStateTextBox.SetFocus()
                self.oldStateTextBox.Refresh()
                return False
            else:
                # check if file has .dcx extension
                if not self.oldStateTextBox.GetValue().lower().endswith(".dcx"):
                    wx.MessageBox("The file must have a .dcx extension.\nVerify your spelling and format or use the directory dialog.", "Error")
                    self.oldStateTextBox.SetBackgroundColour("pink")
                    self.oldStateTextBox.SetFocus()
                    self.oldStateTextBox.Refresh()
                    return False
                else:
                    return True

    def validateNewState(self):
        # check if textbox is empty
        if len(self.newStateTextBox.GetValue()) == 0:
            wx.MessageBox("Please enter a file name.", "Error")
            self.newStateTextBox.SetBackgroundColour("pink")
            self.newStateTextBox.SetFocus()
            self.newStateTextBox.Refresh()
            return False
        else:
            self.newStateTextBox.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            self.newStateTextBox.Refresh()
            
            # check if filename is valid (only alphanumeric, hypen, underscore allowed)
            if re.search(r'[^A-Za-z0-9_.\-\\]',self.newStateTextBox.GetValue()):
                wx.MessageBox("Filename can only contain letters, numbers, hyphens, and underscores. Please try again.", "Error")
                self.newStateTextBox.SetBackgroundColour("pink")
                self.newStateTextBox.SetFocus()
                self.newStateTextBox.Refresh()
                return False
            else:
                return True
            
    def validateOutputDir(self):
        # check if textbox is empty
        if len(self.outputDirTextBox.GetValue()) == 0:
            wx.MessageBox("Please enter an output directory.", "Error")
            self.outputDirTextBox.SetBackgroundColour("pink")
            self.outputDirTextBox.SetFocus()
            self.outputDirTextBox.Refresh()
            return False
        else:
            self.outputDirTextBox.SetBackgroundColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            self.outputDirTextBox.Refresh()
            
            # check if directory exists
            if not os.path.exists("%s" % self.outputDirTextBox.GetValue()):
                wx.MessageBox("The directory does not exist.\nVerify your spelling and format or use the directory dialog.", "Error")
                self.outputDirTextBox.SetBackgroundColour("pink")
                self.outputDirTextBox.SetFocus()
                self.outputDirTextBox.Refresh()
                return False
            else:
                return True
            
if __name__ == "__main__":
    app = wx.App(False)
    gui = GUI(None)
    gui.Show()
    app.MainLoop()