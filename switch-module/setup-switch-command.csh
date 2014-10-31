if ($?tcsh) then
  set modules_shell="tcsh"
else
  set modules_shell="csh"
endif

alias switch-modules 'eval `BASE/switch/switch_modules.csh $modules_shell \!*` '
