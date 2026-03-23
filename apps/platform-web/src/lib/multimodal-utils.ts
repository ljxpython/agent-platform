import { ContentBlock } from "@langchain/core/messages";

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = "";
  const bytes = new Uint8Array(buffer);

  for (const byte of bytes) {
    binary += String.fromCharCode(byte);
  }

  return btoa(binary);
}

export async function fileToContentBlock(
  file: File,
): Promise<ContentBlock.Multimodal.Data> {
  const base64 = arrayBufferToBase64(await file.arrayBuffer());

  if (file.type === "application/pdf") {
    return {
      type: "file",
      data: base64,
      mimeType: file.type,
      metadata: {
        filename: file.name,
        name: file.name,
      },
    };
  }

  return {
    type: "image",
    data: base64,
    mimeType: file.type,
    metadata: {
      name: file.name,
      filename: file.name,
    },
  };
}

export function isBase64ContentBlock(
  block: unknown,
): block is ContentBlock.Multimodal.Data {
  if (!block || typeof block !== "object") {
    return false;
  }

  const candidate = block as ContentBlock.Multimodal.Data;
  return (
    typeof candidate.type === "string" &&
    typeof candidate.data === "string" &&
    typeof candidate.mimeType === "string"
  );
}
