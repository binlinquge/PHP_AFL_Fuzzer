<?php
ini_set('xdebug.trace_output_dir', '/home/abeer/log');
ini_set('xdebug.trace_output_name','trace');
ini_set('xdebug.auto_trace', 'On');
ini_set('xdebug.collect_params', 4);
xdebug_start_code_coverage();
xdebug_start_trace();

///////////////////////////////
//   CONNECT TO DATABASE     //
// allows system to connect  //
// to the database it uses   //
///////////////////////////////



 $dbcnx = mysql_connect($dbaddress,$dbuser,$dbpass)
                                         or die("Could not connect: " . mysql_error());


 mysql_select_db($dbname, $dbcnx) or die ('Unable to select the database: ' . mysql_error());

 require_once("DBFunctions.php");
 

file_put_contents('/home/abeer/log/codeCoverage.txt' , var_export(xdebug_get_code_coverage(), true) );
?>

