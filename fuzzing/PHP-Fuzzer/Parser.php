<?php

/*
 * This file is part of Twig.
 *
 * (c) Fabien Potencier
 * (c) Armin Ronacher
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Twig;

use Twig\Error\SyntaxError;
use Twig\Node\BlockNode;
use Twig\Node\BlockReferenceNode;
use Twig\Node\BodyNode;
use Twig\Node\Expression\AbstractExpression;
use Twig\Node\MacroNode;
use Twig\Node\ModuleNode;
use Twig\Node\Node;
use Twig\Node\NodeCaptureInterface;
use Twig\Node\NodeOutputInterface;
use Twig\Node\PrintNode;
use Twig\Node\TextNode;
use Twig\TokenParser\TokenParserInterface;

/**
 * @author Fabien Potencier <fabien@symfony.com>
 */
class Parser
{
    private $stack = [];
    private $stream;
    private $parent;
    private $handlers;
    private $visitors;
    private $expressionParser;
    private $blocks;
    private $blockStack;
    private $macros;
    private $env;
    private $importedSymbols;
    private $traits;
    private $embeddedTemplates = [];
    private $varNameSalt = 0;

    public function __construct(Environment $env)
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->env = $env; }
    }

    public function getVarName(): string
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return sprintf('__internal_%s', hash('sha256', __METHOD__.$this->stream->getSourceContext()->getCode().$this->varNameSalt++)); }
    }

    public function parse(TokenStream $stream, $test = null, bool $dropNeedle = false): ModuleNode
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $vars = get_object_vars($this); }
        unset($vars['stack'], $vars['env'], $vars['handlers'], $vars['visitors'], $vars['expressionParser'], $vars['reservedMacroNames']);
        $this->stack[] = $vars;

        // tag handlers
        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null === $this->handlers)) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->handlers = []; }
            foreach ($this->env->getTokenParsers() as $handler) {
                { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $handler->setParser($this); }

                $this->handlers[$handler->getTag()] = $handler;
            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        // node visitors
        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null === $this->visitors)) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->visitors = $this->env->getNodeVisitors(); }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null === $this->expressionParser)) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->expressionParser = new ExpressionParser($this, $this->env); }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        $this->stream = $stream;
        $this->parent = null;
        $this->blocks = [];
        $this->macros = [];
        $this->traits = [];
        $this->blockStack = [];
        $this->importedSymbols = [[]];
        $this->embeddedTemplates = [];
        $this->varNameSalt = 0;

        try {
            $body = $this->subparse($test, $dropNeedle);

            if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null !== $this->parent && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null === $body = $this->filterBodyNodes($body)))) {
                { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $body = new Node(); }
            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 
        } catch (SyntaxError $e) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, !$e->getSourceContext())) {
                { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $e->setSourceContext($this->stream->getSourceContext()); }
            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  }

            if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, !$e->getTemplateLine())) {
                { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $e->setTemplateLine($this->stream->getCurrent()->getLine()); }
            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

            throw $e;
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        $node = new ModuleNode(new BodyNode([$body]), $this->parent, new Node($this->blocks), new Node($this->macros), new Node($this->traits), $this->embeddedTemplates, $stream->getSourceContext());

        $traverser = new NodeTraverser($this->env, $this->visitors);

        $node = $traverser->traverse($node);

        // restore previous stack so previous parse() call can resume working
        foreach (array_pop($this->stack) as $key => $val) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->$key = $val; }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        return $node;
    }

    public function subparse($test, bool $dropNeedle = false): Node
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $lineno = $this->getCurrentToken()->getLine(); }
        $rv = [];
        while (!$this->stream->isEOF()) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  switch ($this->getCurrentToken()->getType()) {
                case /* Token::TEXT_TYPE */ 0:
                    { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $token = $this->stream->next(); }
                    $rv[] = new TextNode($token->getValue(), $token->getLine());
                    break;

                case /* Token::VAR_START_TYPE */ 2:
                    { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $token = $this->stream->next(); }
                    $expr = $this->expressionParser->parseExpression();
                    $this->stream->expect(/* Token::VAR_END_TYPE */ 4);
                    $rv[] = new PrintNode($expr, $token->getLine());
                    break;

                case /* Token::BLOCK_START_TYPE */ 1:
                    { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->stream->next(); }
                    $token = $this->getCurrentToken();

                    if (/* Token::NAME_TYPE */ FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, 5 !== $token->getType())) {
                        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  throw new SyntaxError('A block must start with a tag name.', $token->getLine(), $this->stream->getSourceContext()); }
                    } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

                    if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null !== $test && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $test($token)))) {
                        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $dropNeedle)) {
                            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->stream->next(); }
                        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  }

                        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, 1 === \count($rv))) {
                            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $rv[0]; }
                        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

                        return new Node($rv, [], $lineno);
                    } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

                    if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, !isset($this->handlers[$token->getValue()]))) {
                        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null !== $test)) {
                            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $e = new SyntaxError(sprintf('Unexpected "%s" tag', $token->getValue()), $token->getLine(), $this->stream->getSourceContext()); }

                            if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, \is_array($test) && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, isset($test[0])) && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $test[0] instanceof TokenParserInterface))) {
                                { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $e->appendMessage(sprintf(' (expecting closing tag for the "%s" tag defined near line %s).', $test[0]->getTag(), $lineno)); }
                            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 
                        } else {
                            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $e = new SyntaxError(sprintf('Unknown "%s" tag.', $token->getValue()), $token->getLine(), $this->stream->getSourceContext()); }
                            $e->addSuggestions($token->getValue(), array_keys($this->env->getTags()));
                        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  }

                        throw $e;
                    } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

                    $this->stream->next();

                    $subparser = $this->handlers[$token->getValue()];
                    $node = $subparser->parse($token);
                    if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null !== $node)) {
                        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $rv[] = $node; }
                    } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 
                    break;

                default:
                    { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  throw new SyntaxError('Lexer or parser ended up in unsupported state.', $this->getCurrentToken()->getLine(), $this->stream->getSourceContext()); }
            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  }
        }

        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, 1 === \count($rv))) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $rv[0]; }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        return new Node($rv, [], $lineno);
    }

    public function getBlockStack(): array
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $this->blockStack; }
    }

    public function peekBlockStack()
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return isset($this->blockStack[\count($this->blockStack) - 1]) ? $this->blockStack[\count($this->blockStack) - 1] : null; }
    }

    public function popBlockStack(): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  array_pop($this->blockStack); }
    }

    public function pushBlockStack($name): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->blockStack[] = $name; }
    }

    public function hasBlock(string $name): bool
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return isset($this->blocks[$name]); }
    }

    public function getBlock(string $name): Node
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $this->blocks[$name]; }
    }

    public function setBlock(string $name, BlockNode $value): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->blocks[$name] = new BodyNode([$value], [], $value->getTemplateLine()); }
    }

    public function hasMacro(string $name): bool
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return isset($this->macros[$name]); }
    }

    public function setMacro(string $name, MacroNode $node): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->macros[$name] = $node; }
    }

    public function addTrait($trait): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->traits[] = $trait; }
    }

    public function hasTraits(): bool
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return \count($this->traits) > 0; }
    }

    public function embedTemplate(ModuleNode $template)
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $template->setIndex(mt_rand()); }

        $this->embeddedTemplates[] = $template;
    }

    public function addImportedSymbol(string $type, string $alias, string $name = null, AbstractExpression $node = null): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->importedSymbols[0][$type][$alias] = ['name' => $name, 'node' => $node]; }
    }

    public function getImportedSymbol(string $type, string $alias)
    {
        // if the symbol does not exist in the current scope (0), try in the main/global scope (last index)
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $this->importedSymbols[0][$type][$alias] ?? ($this->importedSymbols[\count($this->importedSymbols) - 1][$type][$alias] ?? null); }
    }

    public function isMainScope(): bool
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return 1 === \count($this->importedSymbols); }
    }

    public function pushLocalScope(): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  array_unshift($this->importedSymbols, []); }
    }

    public function popLocalScope(): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  array_shift($this->importedSymbols); }
    }

    public function getExpressionParser(): ExpressionParser
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $this->expressionParser; }
    }

    public function getParent(): ?Node
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $this->parent; }
    }

    public function setParent(?Node $parent): void
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $this->parent = $parent; }
    }

    public function getStream(): TokenStream
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $this->stream; }
    }

    public function getCurrentToken(): Token
    {
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $this->stream->getCurrent(); }
    }

    private function filterBodyNodes(Node $node, bool $nested = false): ?Node
    {
        // check that the body does not contain non-empty output nodes
        { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  if (
            FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, ($node instanceof TextNode && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, !ctype_space($node->getAttribute('data'))))
            ||
            (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, !$node instanceof TextNode && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, !$node instanceof BlockReferenceNode) && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $node instanceof NodeOutputInterface))))
        ) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, false !== strpos((string) $node, \chr(0xEF).\chr(0xBB).\chr(0xBF)))) {
                { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $t = substr($node->getAttribute('data'), 3); }
                if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, '' === $t || FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, ctype_space($t)))) {
                    // bypass empty nodes starting with a BOM
                    { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return null; }
                } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 
            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  }

            throw new SyntaxError('A template that extends another one cannot include content outside Twig blocks. Did you forget to put the content inside a {% block %} tag?', $node->getTemplateLine(), $this->stream->getSourceContext());
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  }

        // bypass nodes that "capture" the output
        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $node instanceof NodeCaptureInterface)) {
            // a "block" tag in such a node will serve as a block definition AND be displayed in place as well
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return $node; }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        // "block" tags that are not captured (see above) are only used for defining
        // the content of the block. In such a case, nesting it does not work as
        // expected as the definition is not part of the default template code flow.
        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $nested && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $node instanceof BlockReferenceNode))) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  throw new SyntaxError('A block definition cannot be nested under non-capturing nodes.', $node->getTemplateLine(), $this->stream->getSourceContext()); }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, $node instanceof NodeOutputInterface)) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  return null; }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        // here, $nested means "being at the root level of a child template"
        // we need to discard the wrapping "Node" for the "body" node
        $nested = $nested || FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, Node::class !== \get_class($node));
        foreach ($node as $k => $n) {
            { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  if (FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null !== $n && FuzzingContext::traceBlock(BLOCK_CONDITION_INDEX_PLACE_HOLDER, null === $this->filterBodyNodes($n, $nested)))) {
                { $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  $node->removeNode($k); }
            } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1;  }
        } $___key = BLOCK_INDEX_PLACE_HOLDER; FuzzingContext::$edges[$___key] = (FuzzingContext::$edges[$___key] ?? 0) + 1; 

        return $node;
    }
}
