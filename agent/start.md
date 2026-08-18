前端
bun --cwd packages/app dev -- --port 4444

后端
bun run --cwd packages/opencode --conditions=browser src/index.ts serve --port 4096

注意，添加skill后需要重启后端。

测试并解决了以下bug:
当前有bug，在主页添加模型api后，已有的对话不能选择新模型，新建的对话可以选择新模型
dialog-connect-provider.tsx 里这个 type="text" 的输入框导致输入apikey明文
设置中很多下拉框，如果做了修改，再次点击，就不会显示下拉框，这也是个bug

