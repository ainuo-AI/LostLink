# 需求图表与代码对应索引

本索引用于从需求规格说明书的图表定位到页面、业务服务和数据存储代码。代码中的 `文档对应：` 注释采用同一组编号。

来源文档：`03_LostLink软件需求规格说明书.docx`，位于项目文件夹的 `成品` 目录。
核对日期：2026-10-13。当前文档包含19张图和1张表。

来源文档 SHA-256：`3ce8f03ec5ea9f22304740a4a177a9e3aca23bcfeda81868814f37a8228df85b`。

## 图表对应

| 文档图表 | 主要代码位置 |
| --- | --- |
| 图2-1 LostLink系统用例模型 | [index.ts::requireAuth](../../frontend/src/router/index.ts#L15)；[dependencies.py::require_admin](../../backend/app/api/dependencies.py#L142) |
| 图2-2-1 用户登录顺序图 | [LoginView.vue::submitLogin](../../frontend/src/views/LoginView.vue#L38)；[auth_service.py::login](../../backend/app/services/auth_service.py#L82) |
| 图2-2-1a 用户注册顺序图 | [RegisterView.vue::submitRegistration](../../frontend/src/views/RegisterView.vue#L25)；[auth_service.py::register](../../backend/app/services/auth_service.py#L65) |
| 图2-2-1b 用户退出顺序图 | [MyView.vue::logout](../../frontend/src/views/MyView.vue#L166)；[auth_service.py::logout](../../backend/app/services/auth_service.py#L149) |
| 图2-2-2 发布失物信息顺序图 | [ItemEntryForm.vue::submit](../../frontend/src/components/ItemEntryForm.vue#L116)；[item_service.py::create_item](../../backend/app/services/item_service.py#L129) |
| 图2-2-3 登记拾物信息顺序图 | [ItemEntryForm.vue::submit](../../frontend/src/components/ItemEntryForm.vue#L116)；[item_service.py::create_item](../../backend/app/services/item_service.py#L129) |
| 图2-2-4 查询物品与查看详情顺序图 | [HomeView.vue::loadItems](../../frontend/src/views/HomeView.vue#L51)；[ItemDetailView.vue::loadItem](../../frontend/src/views/ItemDetailView.vue#L29)；[item_service.py::list_items](../../backend/app/services/item_service.py#L85)；[item_service.py::get_public_item](../../backend/app/services/item_service.py#L119) |
| 图2-2-5 编辑物品记录顺序图 | [MyView.vue::saveEdit](../../frontend/src/views/MyView.vue#L108)；[item_service.py::update_item](../../backend/app/services/item_service.py#L216) |
| 图2-2-5a 结束物品记录顺序图 | [MyView.vue::finishItem](../../frontend/src/views/MyView.vue#L142)；[item_service.py::update_status](../../backend/app/services/item_service.py#L295) |
| 图2-2-6 查看匹配通知顺序图 | [NotificationsView.vue::load](../../frontend/src/views/NotificationsView.vue#L36)；[feature_service.py::list](../../backend/app/services/feature_service.py#L324)；[feature_service.py::get](../../backend/app/services/feature_service.py#L337)；[feature_service.py::mark_read](../../backend/app/services/feature_service.py#L344) |
| 图2-2-7 确认或拒绝匹配顺序图 | [MatchDetailView.vue::decide](../../frontend/src/views/MatchDetailView.vue#L49)；[feature_service.py::feedback](../../backend/app/services/feature_service.py#L351) |
| 图2-2-8 举报物品信息顺序图 | [ReportSubmitView.vue::submitReport](../../frontend/src/views/ReportSubmitView.vue#L80)；[feature_service.py::create](../../backend/app/services/feature_service.py#L164) |
| 图2-2-9 处理举报顺序图 | [AdminConsole.vue::handleReport](../../frontend/src/views/admin/AdminConsole.vue#L86)；[feature_service.py::resolve](../../backend/app/services/feature_service.py#L208) |
| 图2-2-9a 管理普通用户状态顺序图 | [AdminConsole.vue::toggleUser](../../frontend/src/views/admin/AdminConsole.vue#L97)；[feature_service.py::update_user_status](../../backend/app/services/feature_service.py#L505) |
| 图2-2-9b 查询管理概览顺序图 | [AdminConsole.vue::load](../../frontend/src/views/admin/AdminConsole.vue#L55)；[feature_service.py::overview](../../backend/app/services/feature_service.py#L478) |
| 图2-2-9c 查询管理员审计顺序图 | [admin.ts::fetchAuditLogs](../../frontend/src/api/admin.ts#L115)；[feature_service.py::list_audits](../../backend/app/services/feature_service.py#L528) |
| 图2-2-10 形成规则候选顺序图 | [feature_service.py::generate_for_item](../../backend/app/services/feature_service.py#L270)；[feature_service.py::_score](../../backend/app/services/feature_service.py#L397)；[item_repository.py::list_matching_candidates](../../backend/app/repositories/item_repository.py#L182)；[campus_distance.py::distance_similarity](../../backend/app/services/campus_distance.py#L36)；[feature_repository.py::create_match](../../backend/app/repositories/feature_repository.py#L369) |
| 图2-2-10a 可选图文比较顺序图 | [multimodal_matching.py::assess](../../backend/app/integrations/multimodal_matching.py#L52)；[feature_service.py:285](../../backend/app/services/feature_service.py#L285) |
| 图2-3 LostLink 校园失物招领系统分析类图 | [user.py::User](../../backend/app/models/user.py#L28)；[item.py::Item](../../backend/app/models/item.py#L17)；[feature.py::MatchNotification](../../backend/app/models/feature.py#L95)；[feature.py::Report](../../backend/app/models/feature.py#L58) |
| 表1-1 LostLink软件功能描述表 | [ImagePicker.vue::selectFiles](../../frontend/src/components/ImagePicker.vue#L58)；[media.ts::uploadImage](../../frontend/src/api/media.ts#L16)；[feature_service.py::upload](../../backend/app/services/feature_service.py#L74) |

发布失物和登记拾物复用 `ItemEntryForm.submit` 与 `ItemService.create_item`，通过 `lost/found` 类型区分。
图中的边界类主要对应Vue页面和组件，控制类对应Service，实体类对应ORM Model；查询和保存通过Repository实现，HTTP请求经API路由适配。

## 搜索注释

```powershell
rg -n "文档对应|文档范围" backend/app backend/tests frontend/src
```

## 编号和范围

原图2-2-11和图2-2-11a已分别改为图2-2-10形成规则候选、图2-2-10a可选图文比较。
当前文档只保留表1-1；原表2-1和表3-1至表3-3的引用已改为现有用例或3.1节说明。
校准任务和版本管理已从当前需求文档删除，现有实现用 `文档范围：` 说明，避免占用现在的图2-2-10和图2-2-10a编号。
