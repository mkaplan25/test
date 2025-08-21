!define APP_NAME "AlloyCraft"
!define APP_VERSION "1.0.0"
!define PUBLISHER "AlloyCraft Team"
!define APP_MAIN_EXE "alloy_craft.exe"

!include "MUI2.nsh"

; Installer ayarları
Name "${APP_NAME}"
OutFile "AlloyCraft_Setup.exe"
InstallDir "$PROGRAMFILES\${APP_NAME}"
RequestExecutionLevel admin

; Modern UI sayfaları
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

; Uninstaller sayfaları
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

!insertmacro MUI_LANGUAGE "English"

Section "Main Application" SecMain
    SetOutPath "$INSTDIR"
    
    ; Tüm dosyaları kopyala
    File /r "files\*.*"
    
    ; Backend servisini kur
    ExecWait '"$INSTDIR\service.exe" --startup=auto install'
    ExecWait 'sc start AlloyCraftBackend'
    
    ; Başlat menüsü kısayolu
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\${APP_MAIN_EXE}"
    
    ; Masaüstü kısayolu
    CreateShortcut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\${APP_MAIN_EXE}"
    
    ; Registry kayıtları
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayName" "${APP_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "UninstallString" "$INSTDIR\uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "Publisher" "${PUBLISHER}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" "DisplayVersion" "${APP_VERSION}"
    
    ; Uninstaller oluştur
    WriteUninstaller "$INSTDIR\uninstall.exe"
SectionEnd

Section "Uninstall"
    ; Servisi durdur ve kaldır
    ExecWait 'sc stop AlloyCraftBackend'
    ExecWait '"$INSTDIR\service.exe" remove'
    
    ; Dosyaları sil
    RMDir /r "$INSTDIR"
    
    ; Kısayolları sil
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    
    ; Registry kayıtlarını sil
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}"
SectionEnd