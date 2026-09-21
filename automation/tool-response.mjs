export function toolResponse(response) {
  const { blob, ...value } = response.ok ? response.value : {};
  const structured = response.ok ? { ...response, value } : response;
  const artifacts = value.artifacts ?? (value.artifact ? [value.artifact] : []);
  const content = [{ type: 'text', text: JSON.stringify(structured) }];
  if (blob && value.mimeType === 'image/png') content.push({ type: 'image', mimeType: value.mimeType, data: blob });
  content.push(...artifacts.map(item => ({
    type: 'resource_link', uri: item.uri, name: item.artifactId, mimeType: item.mimeType,
  })));
  return { isError: !response.ok, structuredContent: structured, content };
}
