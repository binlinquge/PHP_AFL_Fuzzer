<?php declare(strict_types=1);

namespace PhpFuzzer\Instrumentation;

use PhpParser\Lexer;
use PhpParser\NodeTraverser;
use PhpParser\Parser;
use PhpParser\PrettyPrinter;
use PhpParser\PrettyPrinterAbstract;

final class Instrumentor {
    private Parser $parser;
    private NodeTraverser $traverser;
    private PrettyPrinterAbstract $prettyPrinter;
    private Context $context;

    public function __construct(string $runtimeContextName) {
        $this->parser = new Parser\Php7(new Lexer\Emulative([
            'usedAttributes' => [
                'comments',
                'startLine', 'endLine',
                'startFilePos', 'endFilePos',
            ],
        ]));
        $this->traverser = new NodeTraverser();
        $this->context = new Context($runtimeContextName);
        $this->traverser->addVisitor(new Visitor($this->context));
        $this->prettyPrinter = new PrettyPrinter\Standard();
    }

    public function instrument(string $code, FileInfo $fileInfo): string {
        $mutableStr = new MutableString($code);
        //echo $code;
        $this->context->fileInfo = $fileInfo;
        $this->context->code = $mutableStr;
        $stmts = $this->parser->parse($code);
        $this->traverser->traverse($stmts);
        //echo $$mutableStr->getModifiedString();
        //echo $temp;
        //return "Yaozong";
        return $mutableStr->getModifiedString();
    }
}
