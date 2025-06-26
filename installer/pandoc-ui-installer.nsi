; =====================================================
; Pandoc UI - Professional Windows Installer
; NSIS Modern UI 2 Script for PySide6/Nuitka Application
; =====================================================

!define PRODUCT_NAME "Pandoc UI"
!define PRODUCT_VERSION "1.0.0"
!define PRODUCT_PUBLISHER "pandoc-ui"
!define PRODUCT_WEB_SITE "https://github.com/nerdneilsfield/pandoc-ui"
!define PRODUCT_DIR_REGKEY "Software\Microsoft\Windows\CurrentVersion\App Paths\pandoc-ui.exe"
!define PRODUCT_UNINST_KEY "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY "HKLM"
!define PRODUCT_STARTMENU_REGVAL "NSIS:StartMenuDir"

; Modern UI
!include "MUI2.nsh"
!include "Sections.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "..\resources\icons\app.ico"
!define MUI_UNICON "..\resources\icons\app.ico"

; Custom images (create these files in installer directory)
!define MUI_WELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_UNWELCOMEFINISHPAGE_BITMAP "welcome.bmp"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "header.bmp"
!define MUI_HEADERIMAGE_RIGHT

; Language Selection Dialog Settings
!define MUI_LANGDLL_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_LANGDLL_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_LANGDLL_REGISTRY_VALUENAME "NSIS:Language"

; Welcome page customization
!define MUI_WELCOMEPAGE_TITLE_3LINES
!define MUI_WELCOMEPAGE_TEXT "Setup will guide you through the installation of $(^NameDA).$\r$\n$\r$\nPandoc UI is a professional graphical interface for document format conversion using Pandoc. Convert between Markdown, HTML, PDF, Word, and many other formats with ease.$\r$\n$\r$\nClick Next to continue."

; Finish page customization
!define MUI_FINISHPAGE_TITLE_3LINES
!define MUI_FINISHPAGE_RUN "$INSTDIR\pandoc-ui.exe"
!define MUI_FINISHPAGE_RUN_TEXT "Launch Pandoc UI"
!define MUI_FINISHPAGE_SHOWREADME "$INSTDIR\README.txt"
!define MUI_FINISHPAGE_SHOWREADME_TEXT "Show README"
!define MUI_FINISHPAGE_SHOWREADME_CHECKED
!define MUI_FINISHPAGE_LINK "Visit the Pandoc UI website for support and updates"
!define MUI_FINISHPAGE_LINK_LOCATION "${PRODUCT_WEB_SITE}"

; Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "..\LICENSE"

; Components page with descriptions
!define MUI_COMPONENTSPAGE_SMALLDESC
!insertmacro MUI_PAGE_COMPONENTS

!insertmacro MUI_PAGE_DIRECTORY

; Start Menu configuration
!define MUI_STARTMENUPAGE_NODISABLE
!define MUI_STARTMENUPAGE_DEFAULTFOLDER "${PRODUCT_NAME}"
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "${PRODUCT_UNINST_ROOT_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "${PRODUCT_UNINST_KEY}"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "${PRODUCT_STARTMENU_REGVAL}"

Var StartMenuFolder
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"
!insertmacro MUI_LANGUAGE "SimpChinese"
!insertmacro MUI_LANGUAGE "Japanese"
!insertmacro MUI_LANGUAGE "French"
!insertmacro MUI_LANGUAGE "German"
!insertmacro MUI_LANGUAGE "Spanish"

; Reserve files
!insertmacro MUI_RESERVEFILE_LANGDLL

; Version information
VIProductVersion "${PRODUCT_VERSION}.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "Comments" "Professional document format conversion tool"
VIAddVersionKey /LANG=${LANG_ENGLISH} "CompanyName" "${PRODUCT_PUBLISHER}"
VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalTrademarks" ""
VIAddVersionKey /LANG=${LANG_ENGLISH} "LegalCopyright" "MIT License"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileDescription" "${PRODUCT_NAME} Installer"
VIAddVersionKey /LANG=${LANG_ENGLISH} "FileVersion" "${PRODUCT_VERSION}.0"
VIAddVersionKey /LANG=${LANG_ENGLISH} "ProductVersion" "${PRODUCT_VERSION}.0"

; Installer settings
Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "pandoc-ui-installer-${PRODUCT_VERSION}.exe"
InstallDir "$PROGRAMFILES64\${PRODUCT_NAME}"
InstallDirRegKey HKLM "${PRODUCT_DIR_REGKEY}" ""
ShowInstDetails show
ShowUnInstDetails show
RequestExecutionLevel admin

; Modern installer configuration
BrandingText " "
InstallColors /windows

; Functions
Function .onInit
  ; Language selection
  !insertmacro MUI_LANGDLL_DISPLAY
  
  ; Check Windows version
  ${IfNot} ${AtLeastWin7}
    MessageBox MB_OK|MB_ICONSTOP "This application requires Windows 7 or later."
    Abort
  ${EndIf}
  
  ; Check for existing installation
  ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
  StrCmp $R0 "" done
  
  MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
    "${PRODUCT_NAME} is already installed. $\n$\nClick 'OK' to remove the previous version or 'Cancel' to cancel this upgrade." \
    /SD IDOK IDOK uninst
  Abort
  
uninst:
  ClearErrors
  ExecWait '$R0 /S _?=$INSTDIR'
  IfErrors no_remove_uninstaller done
  
no_remove_uninstaller:
done:
FunctionEnd

; Main application section
SectionGroup "Pandoc UI Application" SecGroupMain

Section "!Core Application" SecMain
  SectionIn RO
  SetOutPath "$INSTDIR"
  SetOverwrite ifnewer
  
  ; Install main executable
  File "..\dist\windows\pandoc-ui-windows-${PRODUCT_VERSION}.exe"
  Rename "$INSTDIR\pandoc-ui-windows-${PRODUCT_VERSION}.exe" "$INSTDIR\pandoc-ui.exe"
  
  ; Install documentation
  File "..\README.md"
  File "..\LICENSE"
  Rename "$INSTDIR\README.md" "$INSTDIR\README.txt"
  
  ; Install icon for shortcuts
  File "..\resources\icons\app.ico"
  
  ; Create application data directory
  CreateDirectory "$LOCALAPPDATA\${PRODUCT_NAME}"
  
  ; Install Visual C++ redistributable if needed
  Call InstallVCRedist
  
SectionEnd

Section "File Associations" SecFileAssoc
  
  ; Markdown files
  WriteRegStr HKCR ".md" "" "PandocUI.MarkdownFile"
  WriteRegStr HKCR ".markdown" "" "PandocUI.MarkdownFile"
  WriteRegStr HKCR "PandocUI.MarkdownFile" "" "Markdown Document"
  WriteRegStr HKCR "PandocUI.MarkdownFile\DefaultIcon" "" "$INSTDIR\app.ico,0"
  WriteRegStr HKCR "PandocUI.MarkdownFile\shell\open" "" "Convert with Pandoc UI"
  WriteRegStr HKCR "PandocUI.MarkdownFile\shell\open\command" "" '"$INSTDIR\pandoc-ui.exe" "%1"'
  WriteRegStr HKCR "PandocUI.MarkdownFile\shell\convert" "" "Convert to..."
  WriteRegStr HKCR "PandocUI.MarkdownFile\shell\convert\command" "" '"$INSTDIR\pandoc-ui.exe" "--convert" "%1"'
  
  ; reStructuredText files
  WriteRegStr HKCR ".rst" "" "PandocUI.RestructuredText"
  WriteRegStr HKCR "PandocUI.RestructuredText" "" "reStructuredText Document"
  WriteRegStr HKCR "PandocUI.RestructuredText\DefaultIcon" "" "$INSTDIR\app.ico,0"
  WriteRegStr HKCR "PandocUI.RestructuredText\shell\open\command" "" '"$INSTDIR\pandoc-ui.exe" "%1"'
  
  ; LaTeX files
  WriteRegStr HKCR ".tex" "PandocUI_backup" ""
  ReadRegStr $R0 HKCR ".tex" ""
  StrCmp $R0 "PandocUI.LaTeXFile" skip_tex_backup
  WriteRegStr HKCR ".tex" "PandocUI_backup" "$R0"
  skip_tex_backup:
  WriteRegStr HKCR ".tex" "" "PandocUI.LaTeXFile"
  WriteRegStr HKCR "PandocUI.LaTeXFile" "" "LaTeX Document"
  WriteRegStr HKCR "PandocUI.LaTeXFile\DefaultIcon" "" "$INSTDIR\app.ico,0"
  WriteRegStr HKCR "PandocUI.LaTeXFile\shell\pandocui" "" "Convert with Pandoc UI"
  WriteRegStr HKCR "PandocUI.LaTeXFile\shell\pandocui\command" "" '"$INSTDIR\pandoc-ui.exe" "%1"'
  
  ; HTML files (add to existing association)
  WriteRegStr HKCR "htmlfile\shell\pandocui" "" "Convert with Pandoc UI"
  WriteRegStr HKCR "htmlfile\shell\pandocui\command" "" '"$INSTDIR\pandoc-ui.exe" "%1"'
  
  ; Refresh shell associations
  System::Call 'shell32.dll::SHChangeNotify(l, l, i, i) v (0x08000000, 0, 0, 0)'
  
SectionEnd

SectionGroupEnd

; Desktop integration
SectionGroup "Desktop Integration" SecGroupDesktop

Section "Desktop Shortcut" SecDesktop
  CreateShortCut "$DESKTOP\${PRODUCT_NAME}.lnk" "$INSTDIR\pandoc-ui.exe" "" "$INSTDIR\app.ico" 0 SW_SHOWNORMAL ALT|CONTROL|SHIFT|F1 "Launch ${PRODUCT_NAME}"
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
  !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
  
  CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\${PRODUCT_NAME}.lnk" "$INSTDIR\pandoc-ui.exe" "" "$INSTDIR\app.ico" 0
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall ${PRODUCT_NAME}.lnk" "$INSTDIR\uninst.exe"
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\${PRODUCT_NAME} Documentation.lnk" "$INSTDIR\README.txt"
  CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Visit Website.lnk" "${PRODUCT_WEB_SITE}"
  
  !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

Section "Context Menu Integration" SecContext
  ; Add "Convert with Pandoc UI" to file context menu
  WriteRegStr HKCR "*\shell\PandocUI" "" "Convert with Pandoc UI"
  WriteRegStr HKCR "*\shell\PandocUI" "Icon" "$INSTDIR\app.ico,0"
  WriteRegStr HKCR "*\shell\PandocUI\command" "" '"$INSTDIR\pandoc-ui.exe" "%1"'
  
  ; Add folder context menu for batch conversion
  WriteRegStr HKCR "Directory\shell\PandocUI" "" "Batch Convert with Pandoc UI"
  WriteRegStr HKCR "Directory\shell\PandocUI" "Icon" "$INSTDIR\app.ico,0"
  WriteRegStr HKCR "Directory\shell\PandocUI\command" "" '"$INSTDIR\pandoc-ui.exe" "--batch" "%1"'
  
  ; Add to Background context menu (right-click on empty space)
  WriteRegStr HKCR "Directory\Background\shell\PandocUI" "" "Open Pandoc UI here"
  WriteRegStr HKCR "Directory\Background\shell\PandocUI" "Icon" "$INSTDIR\app.ico,0"
  WriteRegStr HKCR "Directory\Background\shell\PandocUI\command" "" '"$INSTDIR\pandoc-ui.exe" "--path" "%V"'
SectionEnd

SectionGroupEnd

; Advanced features
SectionGroup /e "Advanced Features" SecGroupAdvanced

Section "Quick Launch Toolbar" SecQuickLaunch
  CreateShortCut "$QUICKLAUNCH\${PRODUCT_NAME}.lnk" "$INSTDIR\pandoc-ui.exe" "" "$INSTDIR\app.ico" 0
SectionEnd

Section "Windows Terminal Integration" SecTerminal
  ; Add to Windows Terminal context menu
  WriteRegStr HKCR "Directory\shell\wt_pandocui" "" "Open Pandoc UI in Terminal"
  WriteRegStr HKCR "Directory\shell\wt_pandocui" "Icon" "$INSTDIR\app.ico,0"
  WriteRegStr HKCR "Directory\shell\wt_pandocui\command" "" 'wt.exe -d "%1" pandoc-ui'
SectionEnd

SectionGroupEnd

; Installation completion
Section -AdditionalIcons
  WriteIniStr "$INSTDIR\${PRODUCT_NAME}.url" "InternetShortcut" "URL" "${PRODUCT_WEB_SITE}"
SectionEnd

Section -Post
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_DIR_REGKEY}" "" "$INSTDIR\pandoc-ui.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayIcon" "$INSTDIR\pandoc-ui.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "InstallLocation" "$INSTDIR"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "InstallSource" "$EXEDIR"
  
  ; Estimate install size
  ${GetSize} "$INSTDIR" "/S=0K" $0 $1 $2
  IntFmt $0 "0x%08X" $0
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "EstimatedSize" "$0"
  
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "NoModify" 1
  WriteRegDWORD ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "NoRepair" 1
  
  ; Register with Windows Features
  WriteRegStr HKLM "SOFTWARE\${PRODUCT_PUBLISHER}\${PRODUCT_NAME}" "Version" "${PRODUCT_VERSION}"
  WriteRegStr HKLM "SOFTWARE\${PRODUCT_PUBLISHER}\${PRODUCT_NAME}" "InstallDir" "$INSTDIR"
SectionEnd

; Section descriptions
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecMain} "Core application files (required)"
!insertmacro MUI_DESCRIPTION_TEXT ${SecFileAssoc} "Associate document files with Pandoc UI for easy opening"
!insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} "Create desktop shortcut for quick access"
!insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} "Create Start Menu shortcuts and program group"
!insertmacro MUI_DESCRIPTION_TEXT ${SecContext} "Add context menu integration for files and folders"
!insertmacro MUI_DESCRIPTION_TEXT ${SecQuickLaunch} "Add shortcut to Quick Launch toolbar"
!insertmacro MUI_DESCRIPTION_TEXT ${SecTerminal} "Add Windows Terminal integration"
!insertmacro MUI_FUNCTION_DESCRIPTION_END

; Helper function to install Visual C++ Redistributable
Function InstallVCRedist
  ; Check if Visual C++ 2019+ redistributable is installed
  ReadRegStr $R0 HKLM "SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64" "Version"
  StrCmp $R0 "" install_vcredist check_version
  
  check_version:
  ; Check if version is sufficient (14.20 or later)
  ; For simplicity, we'll skip this detailed check in this example
  Goto vcredist_ok
  
  install_vcredist:
  MessageBox MB_YESNO|MB_ICONQUESTION \
    "This application requires Microsoft Visual C++ Redistributable.$\n$\nWould you like to download and install it now?" \
    /SD IDYES IDNO vcredist_skip
  
  ; Download and install VC++ redistributable
  ; In a real scenario, you might include the redistributable in your installer
  ExecShell "open" "https://aka.ms/vs/17/release/vc_redist.x64.exe"
  
  vcredist_skip:
  vcredist_ok:
FunctionEnd

; Uninstaller
Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 \
    "Are you sure you want to completely remove $(^Name) and all of its components?" \
    /SD IDYES IDYES +2
  Abort
FunctionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK \
    "$(^Name) was successfully removed from your computer." \
    /SD IDOK
FunctionEnd

Section Uninstall
  ; Remove files and folders
  Delete "$INSTDIR\pandoc-ui.exe"
  Delete "$INSTDIR\README.txt"
  Delete "$INSTDIR\LICENSE"
  Delete "$INSTDIR\app.ico"
  Delete "$INSTDIR\${PRODUCT_NAME}.url"
  Delete "$INSTDIR\uninst.exe"
  
  ; Remove shortcuts
  Delete "$DESKTOP\${PRODUCT_NAME}.lnk"
  Delete "$QUICKLAUNCH\${PRODUCT_NAME}.lnk"
  
  ; Remove Start Menu entries
  !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
  Delete "$SMPROGRAMS\$StartMenuFolder\${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall ${PRODUCT_NAME}.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\${PRODUCT_NAME} Documentation.lnk"
  Delete "$SMPROGRAMS\$StartMenuFolder\Visit Website.lnk"
  RMDir "$SMPROGRAMS\$StartMenuFolder"
  
  ; Remove file associations
  DeleteRegKey HKCR "PandocUI.MarkdownFile"
  DeleteRegKey HKCR "PandocUI.RestructuredText"
  DeleteRegKey HKCR "PandocUI.LaTeXFile"
  
  ; Restore LaTeX file association if we backed it up
  ReadRegStr $R0 HKCR ".tex" "PandocUI_backup"
  StrCmp $R0 "" skip_tex_restore
  WriteRegStr HKCR ".tex" "" "$R0"
  DeleteRegValue HKCR ".tex" "PandocUI_backup"
  skip_tex_restore:
  
  DeleteRegValue HKCR ".md" ""
  DeleteRegValue HKCR ".markdown" ""
  DeleteRegValue HKCR ".rst" ""
  
  ; Remove context menu entries
  DeleteRegKey HKCR "*\shell\PandocUI"
  DeleteRegKey HKCR "Directory\shell\PandocUI"
  DeleteRegKey HKCR "Directory\Background\shell\PandocUI"
  DeleteRegKey HKCR "htmlfile\shell\pandocui"
  DeleteRegKey HKCR "Directory\shell\wt_pandocui"
  
  ; Remove registry entries
  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  DeleteRegKey HKLM "${PRODUCT_DIR_REGKEY}"
  DeleteRegKey HKLM "SOFTWARE\${PRODUCT_PUBLISHER}\${PRODUCT_NAME}"
  
  ; Remove installation directory
  RMDir "$INSTDIR"
  
  ; Clean up application data
  RMDir /r "$LOCALAPPDATA\${PRODUCT_NAME}"
  
  ; Refresh shell associations
  System::Call 'shell32.dll::SHChangeNotify(l, l, i, i) v (0x08000000, 0, 0, 0)'
  
  SetAutoClose true
SectionEnd

; Include additional utilities
!include "FileFunc.nsh"
!insertmacro GetSize