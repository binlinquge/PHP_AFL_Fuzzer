<?php
ini_set('xdebug.trace_output_dir', '/home/abeer/log');
ini_set('xdebug.trace_output_name','trace');
ini_set('xdebug.auto_trace', 'On');
ini_set('xdebug.collect_params', 4);
xdebug_start_code_coverage();
xdebug_start_trace();

 print("<body>");

 include("maketop.php");

 print("
 <tr>
  <td class='b' width=100 valign='top'>
   <br><br>
   <a class='menu' href='index.php'>Home</a>
   <br><br>
   <a class='menu' href='index.php'>About Us</a>
  </td>
  <td class='b' width=10 background='./images/left.gif'>&nbsp;</td>
  <td class='w' valign='top'>
   <table border=0 cellspacing=0 cellpadding=25 width='100%' height='100%'>
	<tr>
	 <td valign='top'>
	  12345
	 </td>
	</tr>
   </table>

  </td>
  <td class='b' width=10 background='./images/right.gif'>&nbsp;</td>
 </tr>
 <tr>
  <td class='b' width=150 height='10'><empty></td>
  <td class='b' width=10  height='10' background='./images/bottomleft.gif'><empty></td>
  <td class='b' width='*' height='10' background='./images/bottom.gif'><empty></td>
  <td class='b' width=10  height='10' background='./images/bottomright.gif'><empty></td>
 </tr>");



file_put_contents('/home/abeer/log/codeCoverage.txt' , var_export(xdebug_get_code_coverage(), true) );
?>
