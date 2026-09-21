import * as nativeApi from "./api";
import { AppView } from "./views/AppView";
import { useWorkspace } from "./workspace/useWorkspace";

export function App({ bridge = nativeApi }: { bridge?: typeof nativeApi } = {}) {
  const model = useWorkspace(bridge);
  return <AppView model={model} />;
}
