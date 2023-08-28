set GNUDIR=C:\ATP\atpdraw\ATP\
%GNUDIR%tpbig.exe both %1 s -r

IF EXIST "*.dbg" (del *.dbg)
IF EXIST "dum*.bin" (del dum*.bin)
IF EXIST "*.tmp" (del *.tmp)
PAUSE