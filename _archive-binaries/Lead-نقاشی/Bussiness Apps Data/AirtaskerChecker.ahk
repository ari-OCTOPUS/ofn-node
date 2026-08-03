SetTimer, CheckJobs, 10000

CheckJobs:
FileRead, newText, C:\Temp\latest_job.txt
FileRead, oldText, C:\Temp\last_job.txt

if (newText != oldText) {
    FileDelete, C:\Temp\last_job.txt
    FileCopy, C:\Temp\latest_job.txt, C:\Temp\last_job.txt
    Run, https://maker.ifttt.com/trigger/Asal/json/with/key/cU_q_dmSR6ulPdEqTOOjsR
}
return
