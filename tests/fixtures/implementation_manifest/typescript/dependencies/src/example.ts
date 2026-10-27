import path from 'node:path';

export function examplePath(exampleRoot: string): string {
    return path.join(exampleRoot, 'example');
}
