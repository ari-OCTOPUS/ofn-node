$ErrorActionPreference = 'Continue'
# 1) command lines of python processes
Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object {
  $cmd = $_.CommandLine
  if ($cmd -and $cmd.Length -gt 130) { $cmd = $cmd.Substring(0,130) }
  "{0}  {1}" -f $_.ProcessId, $cmd
}
""
# 2) Restart Manager: which processes hold handles on chrono.db
Add-Type @'
using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public static class RM {
  [StructLayout(LayoutKind.Sequential)] struct RM_UNIQUE_PROCESS { public int dwProcessId; public System.Runtime.InteropServices.ComTypes.FILETIME ProcessStartTime; }
  const int RmRebootReasonNone = 0; const int CCH_RM_MAX_APP_NAME = 255; const int CCH_RM_MAX_SVC_NAME = 63;
  enum RM_APP_TYPE { RmUnknownApp = 0, RmMainWindow = 1, RmOtherWindow = 2, RmService = 3, RmExplorer = 4, RmConsole = 5, RmCritical = 1000 }
  [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)] struct RM_PROCESS_INFO {
    public RM_UNIQUE_PROCESS Process;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCH_RM_MAX_APP_NAME + 1)] public string strAppName;
    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = CCH_RM_MAX_SVC_NAME + 1)] public string strServiceShortName;
    public RM_APP_TYPE ApplicationType; public uint AppStatus; public uint TSSessionId; [MarshalAs(UnmanagedType.Bool)] public bool bRestartable;
  }
  [DllImport("rstrtmgr.dll", CharSet = CharSet.Unicode)] static extern int RmRegisterResources(uint pSessionHandle, uint nFiles, string[] rgsFilenames, uint nApplications, [In] RM_UNIQUE_PROCESS[] rgApplications, uint nServices, string[] rgsServiceNames);
  [DllImport("rstrtmgr.dll", CharSet = CharSet.Auto)] static extern int RmStartSession(out uint pSessionHandle, int dwSessionFlags, string strSessionKey);
  [DllImport("rstrtmgr.dll")] static extern int RmEndSession(uint pSessionHandle);
  [DllImport("rstrtmgr.dll")] static extern int RmGetList(uint dwSessionHandle, out uint pnProcInfoNeeded, ref uint pnProcInfo, [In, Out] RM_PROCESS_INFO[] rgAffectedApps, ref uint lpdwRebootReasons);
  public static List<int> WhoLocks(string path) {
    uint handle; List<int> procs = new List<int>();
    string key = Guid.NewGuid().ToString();
    if (RmStartSession(out handle, 0, key) != 0) return procs;
    try {
      if (RmRegisterResources(handle, 1, new string[] { path }, 0, null, 0, null) == 0) {
        uint needed = 0, count = 10; RM_PROCESS_INFO[] info = new RM_PROCESS_INFO[count]; uint reasons;
        int res = RmGetList(handle, out needed, ref count, info, ref reasons);
        if (res == 0) { for (int i = 0; i < count; i++) procs.Add(info[i].Process.dwProcessId); }
      }
    } finally { RmEndSession(handle); }
    return procs;
  }
}
'@
$target = 'F:\backup\_ops\state\chrono.db'
"RM lockers of ${target}:"
$locks = [RM]::WhoLocks($target)
if ($locks.Count -eq 0) { "  (none reported)" } else { $locks | ForEach-Object { "  PID $_" } }
