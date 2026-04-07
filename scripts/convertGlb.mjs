import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { dedup } from '@gltf-transform/functions';
import sharp from 'sharp';
import draco3d from 'draco3dgltf';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';

const [input, output] = process.argv.slice(2);

if (!input || !output) {
    console.log('Usage: node convertGlb.mjs input.glb output.glb');
    process.exit(1);
}

const DRACO_ENCODER = await draco3d.createEncoderModule();
const DRACO_DECODER = await draco3d.createDecoderModule();

const io = new NodeIO()
    .registerExtensions(ALL_EXTENSIONS)
    .registerDependencies({
        'draco3d.decoder': DRACO_DECODER,
        'draco3d.encoder': DRACO_ENCODER,
        'meshopt.decoder': MeshoptDecoder,
        'meshopt.encoder': MeshoptEncoder,
    });

const doc = await io.read(input);

for (const texture of doc.getRoot().listTextures()) {
    if (texture.getMimeType() === 'image/webp') {
        const webpData = texture.getImage();
        const meta = await sharp(webpData).metadata();
        const hasAlpha = meta.channels === 4;

        // Check nếu texture là normal map (theo convention đặt tên)
        const name = texture.getName() || '';
        const isNormal = /normal/i.test(name);

        let converted, mime, ext;
        if (hasAlpha || isNormal) {
            converted = await sharp(webpData).png().toBuffer();
            mime = 'image/png';
            ext = 'PNG';
        } else {
            converted = await sharp(webpData).jpeg({ quality: 90 }).toBuffer();
            mime = 'image/jpeg';
            ext = 'JPG';
        }

        texture.setImage(converted);
        texture.setMimeType(mime);
    }
}

// Xóa extensions không cần nữa
for (const ext of doc.getRoot().listExtensionsUsed()) {
    if (ext.extensionName === 'EXT_texture_webp') {
        ext.dispose();
    }
}

await doc.transform(dedup());
await io.write(output, doc);