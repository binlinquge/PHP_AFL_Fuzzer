<?php
ini_set('xdebug.trace_output_dir', '/home/abeer/log');
ini_set('xdebug.trace_output_name','trace');
ini_set('xdebug.auto_trace', 'On');
ini_set('xdebug.collect_params', 4);
xdebug_start_code_coverage();
xdebug_start_trace();


 print("<h1>Add New Term</h1>

  <form name='addterm' action='./index.php' method='POST'>
  <br><br><br>
  <table cellspacing='0' cellpadding='5' class='dynamiclist' align='center' width='600'>
   <tr class='header'>
	<th>Term Name</th>
	<th>Start Date</th>
	<th>End Date</th>
   </tr>
   <tr class='even'>
	<td><input type='text' name='title' maxlength='15' /></td>
	<td><input type='text' name='startdate' maxlength='10' size='10' /></td>
	<td><input type='text' name='enddate' maxlength='10' size='10' /></td>
   </tr>
   </table>

   <br>

   <table cellpadding='0' border='0' align='center' width='600'>
   <tr>
   <td><input type='button' value='Add Term' onClick='document.addterm.addterm.value=1;document.addterm.page2.value=6;document.addterm.submit();'> <input type='button' value='Cancel' onClick='document.addterm.page2.value=6;document.addterm.submit();'></td>
   </tr>
   </table>

  <input type='hidden' name='addterm' value=''>
  <input type='hidden' name='page2' value='$page2'>
  <input type='hidden' name='logout'>
  <input type='hidden' name='page' value='$page'>

 </form>

 <table width='520' border=0 cellspacing=0 cellpadding=0 height=1>
  <tr>
   <td valign='top'>
	&nbsp;
   </td>
  </tr>
 </table>
 ");

file_put_contents('/home/abeer/log/codeCoverage.txt' , var_export(xdebug_get_code_coverage(), true) );
?>
