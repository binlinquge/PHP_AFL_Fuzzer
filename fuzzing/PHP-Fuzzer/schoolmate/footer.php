<?php
ini_set('xdebug.trace_output_dir', '/home/abeer/log');
ini_set('xdebug.trace_output_name','trace');
ini_set('xdebug.auto_trace', 'On');
ini_set('xdebug.collect_params', 4);
xdebug_start_code_coverage();
xdebug_start_trace();

 print("
   <td class='bv' width=10 background='./images/right.gif'>&nbsp;&nbsp;</font></td>
 </tr>
 <tr>
  <td class='b' width=130 height='10'><empty></td>
  <td class='b' width=10  height='10' background='./images/bottomleft.gif'><empty></td>
  <td class='b' height='10' background='./images/bottom.gif'><empty></td>
  <td class='b' width=10  height='10' background='./images/bottomright.gif'><empty></td>
 </tr>
 <tr>
  <td colspan=4 bgColor='#336699' height='20'>
   <center>
    <span class='footer'>Powered By - </span><a target='_BLANK' href='http://www.primateapplications.com' class='footer'>SchoolMate</a>
   <center>
  </td>
 </tr>
 </table>
 </body>
 </html>");

file_put_contents('/home/abeer/log/codeCoverage.txt' , var_export(xdebug_get_code_coverage(), true) );
?>
