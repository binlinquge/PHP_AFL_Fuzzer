<?php
ini_set('xdebug.trace_output_dir', '/home/abeer/log');
ini_set('xdebug.trace_output_name','trace');
ini_set('xdebug.auto_trace', 'On');
ini_set('xdebug.collect_params', 4);
xdebug_start_code_coverage();
xdebug_start_trace();


 $query = mysql_query("select password from users where username = \"" . $_POST["username"] . "\"")
          or die("Unable to validate login and password with the database: " . mysql_error());

 $result = mysql_fetch_array($query);
 $result = $result[0];

 if(md5($_POST["password"]) != $result)
 {
  $loginerror = 1;
  $page = 0;
 }
 else
 {
  $_SESSION["username"] = $_POST["username"];

  //Get user's type//
  $query = mysql_query("select type from users where username = '$_SESSION[username]'")
		   or die("Unable to get user type: " . mysql_error());

  $_SESSION["usertype"] = mysql_result($query,0);

  //Get user's ID//

  $query = mysql_query("select userid from users where username = '$_SESSION[username]'")
		   or die("Unable to get userid from users: " . mysql_error());

  $_SESSION["userid"] = mysql_result($query,0);
  session_start();

  switch ($_SESSION["usertype"])
  {
	case "Admin":
		  $page = 1;
		  $page2 =0;
		  
		  break;

	case "Teacher":
		  $page = 2;
		  $page2 =0;
		  
		  break;

	case "Substitute":
		  $page = 2;
		  $page2 =0;
		 
		  break;

	case "Student":
		  $page = 4;
		  $page2 =0;
		  
		  break;

	case "Parent":
		  $page = 5;
          $page2 =0;

		  break;

	default:
		  die("ValidateLogin.php: Unable to determine the type of user.  Please verify.");

		  break;
  }
 }


file_put_contents('/home/abeer/log/codeCoverage.txt' , var_export(xdebug_get_code_coverage(), true) );
?>
