# Git 工作流 Skill

帮助用户进行 Git 操作，包括提交和推送代码。
push之前记得跑通所有测试

## 使用方式

当用户请求提交或推送代码时，按以下步骤操作：

### 1. 查看当前状态

```bash
git status
```

### 2. 添加文件到暂存区

```bash
# 添加所有修改的文件
git add .

# 或添加特定文件
git add <file1> <file2>
```

### 3. 创建提交

```bash
git commit -m "feat: 添加集成测试和真实网站测试"
```

### 4. 推送到远程仓库

```bash
# 推送到当前分支
git push

# 或推送到指定分支
git push origin <branch>
```

## 提交信息格式

使用约定式提交格式：

- `feat:` - 新功能
- `fix:` - 修复 bug
- `docs:` - 文档更新
- `test:` - 测试相关
- `refactor:` - 代码重构
- `chore:` - 构建/工具链相关

## 注意事项

1. 提交前先运行测试确保代码正常
2. 提交信息要清晰描述改动内容
3. 推送前先拉取远程更新：`git pull --rebase`
4. 避免推送敏感信息（API密钥、密码等）
