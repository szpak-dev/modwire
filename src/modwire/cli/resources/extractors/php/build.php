#!/usr/bin/env php
<?php

declare(strict_types=1);

$root = __DIR__;
$output = $root . '/script.php';
$pharPath = $root . '/script.phar';

if (file_exists($output)) {
    unlink($output);
}
if (file_exists($pharPath)) {
    unlink($pharPath);
}

$phar = new Phar($pharPath);
$phar->startBuffering();
$phar->setSignatureAlgorithm(Phar::SHA256);
$phar->addFile($root . '/script.src.php', 'script.src.php');
$phar->addFromString('vendor/autoload.php', <<<'PHP'
<?php

spl_autoload_register(function (string $class): void {
    $prefix = 'PhpParser\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }
    $relativePath = str_replace('\\', '/', substr($class, strlen($prefix)));
    require __DIR__ . '/nikic/php-parser/lib/PhpParser/' . $relativePath . '.php';
});
PHP);

$vendorRoot = $root . '/vendor/nikic/php-parser';
$libraryRoot = $vendorRoot . '/lib/PhpParser';
if (!is_dir($libraryRoot)) {
    fwrite(STDERR, "Composer vendor directory is missing. Run composer install first.\n");
    exit(1);
}

$iterator = new RecursiveIteratorIterator(
    new RecursiveDirectoryIterator($libraryRoot, FilesystemIterator::SKIP_DOTS)
);
$paths = [];

foreach ($iterator as $file) {
    if (!$file->isFile()) {
        continue;
    }
    $paths[] = $file->getPathname();
}

sort($paths, SORT_STRING);
$paths[] = $vendorRoot . '/LICENSE';

foreach ($paths as $path) {
    $relativePath = str_replace($root . '/', '', $path);
    $phar->addFile($path, $relativePath);
}

$phar->setStub(<<<'PHP'
#!/usr/bin/env php
<?php
Phar::mapPhar('script.php');
require 'phar://script.php/script.src.php';
__HALT_COMPILER();
PHP);
$phar->stopBuffering();
rename($pharPath, $output);
unset($phar);

$archive = file_get_contents($output);
if ($archive === false) {
    fwrite(STDERR, "Built archive cannot be read.\n");
    exit(1);
}

$stubEnd = strpos($archive, "__HALT_COMPILER(); ?>\r\n");
if ($stubEnd === false) {
    fwrite(STDERR, "Built archive has no Phar stub terminator.\n");
    exit(1);
}

$cursor = $stubEnd + strlen("__HALT_COMPILER(); ?>\r\n");
$cursor += 4;
$fileCount = unpack('Vcount', substr($archive, $cursor, 4))['count'];
$cursor += 10;
$aliasLength = unpack('Vlength', substr($archive, $cursor, 4))['length'];
$cursor += 4 + $aliasLength;
$metadataLength = unpack('Vlength', substr($archive, $cursor, 4))['length'];
$cursor += 4 + $metadataLength;

for ($index = 0; $index < $fileCount; $index++) {
    $nameLength = unpack('Vlength', substr($archive, $cursor, 4))['length'];
    $cursor += 4 + $nameLength + 4;
    $archive = substr_replace($archive, pack('V', 946684800), $cursor, 4);
    $cursor += 16;
    $fileMetadataLength = unpack('Vlength', substr($archive, $cursor, 4))['length'];
    $cursor += 4 + $fileMetadataLength;
}

$unsignedArchive = substr($archive, 0, -40);
$archive = $unsignedArchive . hash('sha256', $unsignedArchive, true) . pack('V', Phar::SHA256) . 'GBMB';
file_put_contents($output, $archive);
chmod($output, 0755);
