<?php
ini_set('xdebug.trace_output_dir', '/home/abeer/log');
ini_set('xdebug.trace_output_name','trace');
ini_set('xdebug.auto_trace', 'On');
ini_set('xdebug.collect_params', 4);
xdebug_start_code_coverage();
xdebug_start_trace();

 print("<table cellpadding=0 cellspacing=0 border=0 width='100%' height='80'>
 <tr>
 <td class='b' width='300'>
  <img src='./images/title.gif' height='75' width='300' />
 </td>
 <td class='b'>
  <table cellpadding=0 cellspacing=0 border=0 width='80%'>
  <tr>
  <td class='b'>
   <div class='yellowtext' align='center'>$schoolname</div>
  </td>
  </tr>
  </table>
 </td>
</tr>
</table>

 <table width='100%' height='88%' border=0 cellspacing=0 cellpadding=0 align='center'>
 <tr>
  <td class='b' width='130' height=10><empty></td>
  <td class='b' width=10 background='./images/topleft.gif'><empty></td>
  <td class='b' height=10 background='./images/top.gif'><empty></td>
  <td class='b' width=10 background='./images/topright.gif'><empty></td>
 </tr>

");

file_put_contents('/home/abeer/log/codeCoverage.txt' , var_export(xdebug_get_code_coverage(), true) );
?>
