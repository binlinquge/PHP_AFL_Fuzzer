<?php
ini_set('xdebug.trace_output_dir', '/home/abeer/log');
ini_set('xdebug.trace_output_name','trace');
ini_set('xdebug.auto_trace', 'On');
ini_set('xdebug.collect_params', 4);
xdebug_start_code_coverage();
xdebug_start_trace();

 // Function to convert the dates into database format //
 function converttodb($indate)
 {
	if($indate == "")
	{
	 $ret_date = "1970-01-01";
	}
	else
	{
	 $date = $indate;
	 list($month, $day, $year) = split('[/.-]', $date);

	 if(strlen($year) == 2 || $year == NULL)
	 {
	  $cur_year = date("Y");
	  $year = $cur_year[0] . $cur_year[1] . $year;
	 }

	 if(strlen($month) < 2 && $month < 10)
	 {
	  $month = "0".$month;
	 }

	 if(strlen($day) < 2 && $day < 10)
	 {
	  $day = "0".$day;
	 }

	 $ret_date = $year."-".$month."-".$day;
	}

	return $ret_date;
 }

 // Convert the database date format into something a bit more readable //
 function convertfromdb($indate)
 {
  list($year, $month, $day) = split('[/.-]', $indate);
  $ret_date = $month."/".$day."/".$year;

  if($ret_date == "01/01/1970")
  {
   $ret_date = "";
  }
  return $ret_date;
 }

file_put_contents('/home/abeer/log/codeCoverage.txt' , var_export(xdebug_get_code_coverage(), true) );
?>

