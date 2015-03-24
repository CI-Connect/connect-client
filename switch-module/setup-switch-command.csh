if ($?tcsh) then
  set modules_shell="tcsh"
else
  set modules_shell="csh"
endif

alias switch_modules 'eval `/tmp/dgc/connect/switch/switch-modules.csh $modules_shell \!*` '
