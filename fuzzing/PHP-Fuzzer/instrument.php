<?php 
namespace PhpFuzzer;
require "./PHP-Fuzzer-master/vendor/autoload.php";


use GetOpt\ArgumentException;
use GetOpt\Command;
use GetOpt\GetOpt;
use GetOpt\Operand;
use GetOpt\Option;
use Nikic\IncludeInterceptor\FileFilter;
use Nikic\IncludeInterceptor\Interceptor;
use PhpFuzzer\Instrumentation\FileInfo;
use PhpFuzzer\Instrumentation\Instrumentor;
use PhpFuzzer\Mutation\Dictionary;
use PhpFuzzer\Mutation\Mutator;
use PhpFuzzer\Mutation\RNG;

//$file_name = "CE-Phoenix-master/contact_us.php";
$file_name = $argv[1];

$code = file_get_contents($file_name);
$fileInfo = new FileInfo();
$instrumentor = new Instrumentor(FuzzingContext::class);
$instrumentedCode = $instrumentor->instrument($code, $fileInfo);

//echo $instrumentedCode;
$f = fopen($argv[2], "w") or die("Unable to open file!");
fwrite($f,$instrumentedCode);
fclose($f);

echo 'Done instrument file '.$file_name.'\n';
?>
