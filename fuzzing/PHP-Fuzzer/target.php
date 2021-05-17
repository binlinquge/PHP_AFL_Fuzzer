<?php // target.php

/** @var PhpFuzzer\Fuzzer $fuzzer */

//require './tolerant-php-parser-master/vendor/autoload.php';
require './tolerant-php-parser-master/vendor/autoload.php';

// Required: The target accepts a single input string and runs it through the tested
//           library. The target is allowed to throw normal Exceptions (which are ignored),
//           but Error exceptions are considered as a found bug.
$parser = new Microsoft\PhpParser\Parser();
$fuzzer->setTarget(function(string $input) use($parser) {
    $parser->parseSourceFile($input);
});

//$fuzzer->loadTarget("../../../CE-Phoenix-master");

// Optional: Many targets don't exhibit bugs on large inputs that can't also be
//           produced with small inputs. Limiting the length may improve performance.
$fuzzer->setMaxLen(1024);
// Optional: A dictionary can be used to provide useful fragments to the fuzzer,
//           such as language keywords. This is particularly important if these
//           cannot be easily discovered by the fuzzer, because they are handled
//           by a non-instrumented PHP extension function such as token_get_all().
$fuzzer->addDictionary('example/php.dict');
?>
