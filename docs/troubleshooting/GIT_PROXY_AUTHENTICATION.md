# Git代理环境下的认证配置问题解决方案

## 问题描述

在配置了网络代理的环境下，使用Git推送代码到GitHub时遇到以下问题：

1. **SSH连接失败**：`Connection closed by 127.0.0.1 port 7897`
2. **HTTPS认证失败**：`fatal: could not read Username for 'https://github.com'`
3. **权限被拒绝**：`remote: Permission to repository.git denied`

## 问题原因分析

### 根本原因
系统配置了SOCKS5代理（127.0.0.1:7897），导致Git的SSH和HTTPS连接都被代理拦截，无法正常访问GitHub。

### 具体问题
1. **系统级代理配置**：macOS网络设置中启用了Web代理和SOCKS代理
2. **Git代理配置冲突**：Git配置与系统代理设置不一致
3. **SSH代理干扰**：SSH连接被代理重定向
4. **认证信息缺失**：没有正确配置GitHub Personal Access Token

## 完整解决方案

### 步骤1：检查现有配置

```bash
# 检查Git代理配置
git config --global --get http.proxy
git config --global --get https.proxy

# 检查远程仓库URL
git remote -v

# 检查系统网络代理设置
networksetup -getwebproxy Wi-Fi
networksetup -getsocksfirewallproxy Wi-Fi
```

### 步骤2：清理冲突的代理配置

```bash
# 清除Git代理配置
git config --global --unset http.proxy
git config --global --unset https.proxy
```

### 步骤3：重新配置Git使用代理

由于网络环境需要代理访问GitHub，重新配置Git使用系统代理：

```bash
# 重新配置Git代理（使用你的代理地址和端口）
git config --global http.proxy socks5://127.0.0.1:7897
git config --global https.proxy socks5://127.0.0.1:7897
```

### 步骤4：配置远程仓库URL

使用HTTPS URL而非SSH，因为SSH在代理环境下更容易出现问题：

```bash
# 切换到HTTPS URL
git remote set-url origin https://github.com/username/repository.git

# 包含用户名的URL（可选）
git remote set-url origin https://username@github.com/username/repository.git
```

### 步骤5：配置GitHub Personal Access Token

#### 5.1 生成Personal Access Token

1. 登录GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. 点击"Generate new token (classic)"
3. 设置token名称和过期时间
4. **必须选择的权限**：
   - `repo` - 完整的仓库访问权限（包括私有仓库）
   - 或者只选择 `public_repo`（仅公共仓库）
5. 生成并复制token

#### 5.2 配置Git凭据存储

```bash
# 启用凭据存储
git config --global credential.helper store
```

#### 5.3 创建凭据文件

创建 `~/.git-credentials` 文件：

```bash
# 创建凭据文件（替换为你的用户名和token）
echo "https://<username>:<your_personal_access_token>@github.com" > ~/.git-credentials
```

示例：
```
https://yourname:ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx@github.com
```

### 步骤6：测试推送

```bash
# 测试推送
git push

# 如果成功，应该看到类似输出：
# To https://github.com/username/repository.git
#    abc123..def456  main -> main
```

## 常见错误及解决方案

### 错误1：`Connection closed by 127.0.0.1 port 7897`

**原因**：SSH连接被代理拦截
**解决**：切换到HTTPS协议，不使用SSH

```bash
git remote set-url origin https://github.com/username/repository.git
```

### 错误2：`fatal: could not read Username/Password`

**原因**：认证信息未正确配置
**解决**：配置凭据存储和Personal Access Token

### 错误3：`remote: Permission denied`

**原因**：Personal Access Token权限不足
**解决**：重新生成token，确保选择了`repo`权限

### 错误4：`Failed to connect to github.com port 443`

**原因**：代理配置错误或网络问题
**解决**：检查代理设置，确保代理服务正常运行

## 最佳实践

### 1. 代理环境下的配置建议

```bash
# 推荐的Git配置
git config --global http.proxy socks5://127.0.0.1:7897
git config --global https.proxy socks5://127.0.0.1:7897
git config --global credential.helper store
```

### 2. 安全注意事项

- **不要在公共环境或版本控制中暴露Personal Access Token**
- **定期轮换Personal Access Token**
- **使用最小权限原则，只授予必要的权限**
- **妥善保管`.git-credentials`文件权限**

```bash
# 设置凭据文件权限
chmod 600 ~/.git-credentials
```

### 3. 多仓库管理

如果需要管理多个Git仓库或不同的GitHub账户，可以使用Git的条件配置：

```bash
# ~/.gitconfig
[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work
[includeIf "gitdir:~/personal/"]
    path = ~/.gitconfig-personal
```

## 配置验证

### 验证步骤

```bash
# 1. 检查Git配置
git config --list | grep proxy
git config --list | grep credential

# 2. 检查远程仓库
git remote -v

# 3. 测试连接
git ls-remote origin

# 4. 测试推送（dry-run）
git push --dry-run
```

### 预期输出

正确配置后，`git push`应该显示：

```
To https://github.com/username/repository.git
   old_commit..new_commit  main -> main
```

## 故障排除检查清单

- [ ] 系统代理设置正确
- [ ] Git代理配置与系统一致
- [ ] 使用HTTPS而非SSH协议
- [ ] Personal Access Token权限充足
- [ ] 凭据存储配置正确
- [ ] 网络连接正常
- [ ] 代理服务运行正常

## 相关配置文件

### Git配置文件位置
- 全局配置：`~/.gitconfig`
- 凭据存储：`~/.git-credentials`
- SSH配置：`~/.ssh/config`

### 关键配置项

```ini
# ~/.gitconfig
[http]
    proxy = socks5://127.0.0.1:7897
[https]
    proxy = socks5://127.0.0.1:7897
[credential]
    helper = store
```

## 备选方案

### 方案1：临时禁用代理

如果代理环境允许，可以临时禁用代理进行Git操作：

```bash
# 临时禁用系统代理
networksetup -setwebproxystate Wi-Fi off
networksetup -setsocksfirewallproxystate Wi-Fi off

# 执行Git操作
git push

# 重新启用代理
networksetup -setwebproxystate Wi-Fi on
networksetup -setsocksfirewallproxystate Wi-Fi on
```

### 方案2：使用GitHub CLI

```bash
# 安装GitHub CLI
brew install gh

# 登录认证
gh auth login

# 使用GitHub CLI推送
gh repo sync
```

## 总结

在代理环境下配置Git需要：

1. **统一代理配置**：确保Git配置与系统代理设置一致
2. **选择合适协议**：在代理环境下HTTPS比SSH更稳定
3. **正确配置认证**：使用Personal Access Token替代密码
4. **妥善管理凭据**：使用Git凭据存储功能

遵循本文档的步骤，可以解决大部分代理环境下的Git认证问题。
