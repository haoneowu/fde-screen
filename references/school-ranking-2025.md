---
title: 2025院校排名离线表与G1使用规则
owner: APU Workshop
status: active
updated: 2026-10-07
ranking_year: 2025
---

## 固定口径

用户于2026-10-07要求长期使用2025版，不随年份自动更新。前150包含第150名及其并列项。只核院校排名资格，不能证明候选人学历真实或替代其他G1条件。

| 适用范围 | 离线文件 | 榜单及覆盖 |
|---|---|---|
| 国内 | [schools-2025-cn.csv](schools-2025-cn.csv) | 2025软科中国大学排名主榜，完整589所，前150共150所 |
| 海外 | [schools-2025-qs.csv](schools-2025-qs.csv) | QS世界大学综合排名2025，前200条；前150含并列共151所，非全球完整榜 |

CSV是唯一数据源，本说明不重复完整院校清单。可用Excel/Numbers打开，也可直接阅读；`rank`保留官方原始名次，`name`保留完整实体名。不要自行把独立学院截为母体校名。

## 国内数据来源及验收

- 发布方：上海软科。
- 官方页面：https://www.shanghairanking.cn/rankings/bcur/2025
- 获取日期：2026-10-07。
- 官方页面公开数据文件：https://www.shanghairanking.cn/_nuxt/static/1789974610/rankings/bcur/2025/payload.js
- 源数据字段验证：`year=2025`，`rankId=11`，`title=中国大学排名（主榜）`，`univData`共589条。
- 保留字段：原始名次、中文完整校名、官方英文校名、官方985/211等标签、官方学校标识；不存无关网页内容或候选人资料。
- 边界：148安徽农业大学、148湖北工业大学、150浙江农林大学、151南通大学。`500+`仍是明确超过150，不是未覆盖。
- 原始payload SHA-256：`3de79e839f76b7e46874de54fedd1853d0a4d81b672d93fcda0a56d602c7dcb9`。
- CSV SHA-256：`5a29751540f8ed69a9742eb96dc97d6cddd30b7a0824f6fc9124643dcc4d0ee9`。

## QS数据来源及限制

- 版本核验：[QS官方2025页](https://www.topuniversities.com/world-university-rankings/2025)，发布日期2024-06-04；获取日期2026-10-07。
- 数据来自[马来西亚理工大学官网托管的QS原署名PDF](https://sps.utm.my/wp-content/uploads/2024/09/2025-QS-World-University-Rankings-2.2-For-qs.com_.pdf)，不是QS域名直接下载。使用2025列，不使用相邻2024列；200条序号连续，保留并列，source_id留空而不冒用行号。
- 按[QS官方更正记录](https://www.topuniversities.com/rankings-release-summaries/world-university-rankings-2025-release-summary)将Washington University in St. Louis修正为176。
- 边界：149 King Abdulaziz University (KAU)；150 Indian Institute of Technology Delhi (IITD)；150 University of Bath；152 Michigan State University及Nagoya University。两所150名已与各自QS官网历史排名核对。
- 前150含并列共151所，另49条超过150；这是全球榜子集，包含中国大陆和港澳台实体，不能据此改变国内/海外路由。
- 未逐校对照全部151个QS院校历史页。中文译名不自动映射；未匹配或未覆盖保持待核验，不得进入通过名单。
- 原始PDF SHA-256：`273540e15ecb64591671b15737057bd460e3c4f8c0a0a7b2076bfb3449d836d6`；CSV SHA-256：`1da69f0adbd32100390ec58ad30ccc525f28f970c84fca6b14feab050029158c`。

## 使用方式

在Skill目录执行（脚本只使用Python标准库，不联网）：

```bash
python3 scripts/school_lookup.py --scope domestic "浙江农林大学" "南通大学" "厦门大学嘉庚学院"
python3 scripts/school_lookup.py --scope overseas "University of Oxford"
```

匹配仅做Unicode全半角、首尾/连续空格和英文大小写归一化；不做子串、模糊搜索、简称猜测或自动中文翻译。未唯一命中时，应核对原始校名、历史更名和实际就读实体，不得自动删掉“学院/校区”等词重试放行。普通校区未知只待核验，不自动排除。

| 查询结果 | 后续处理 |
|---|---|
| `within_top150` | 只说明排名符合；核初始高等教育、就读实体及归属后才可判G1通过 |
| `outside_top150` | 确认初始本科实体匹配后，G1确认不符；后续硕博和经验不补偿 |
| `unmatched` / `ambiguous` | 不进通过名单；区分未覆盖、中文译名、简称、更名或校区问题，向使用者补证 |
| `wrong_scope` / `scope_review` | 国内必须用国内主榜；港澳台及归属不明按G1先请使用者确认 |
| `data_unavailable` / `rank_unresolved` | 数据缺失或名次不明，待核验，不换榜、不猜测 |

榜单未覆盖不等于150名以后。例如财经、医药等类别院校可能不在软科主榜，不能拿类别榜名次混入本规则，也不能仅凭985/211身份放行。需要使用者明确例外或补充适用规则；例外独立记录，不改写为原规则通过。

## HR交付检查

逐人保留：简历学校原文、初始高等教育路径、对应实体、固定榜单与名次、匹配方式、G1状态和补证问题。不保存候选人信息到本Skill。

报告分为“通过/推荐复筛”“待核验”“确认不符”三组，待核验和确认不符不夹在通过名单里。只有六项门槛全部通过才可评分，且评分资料齐全者才可按70分复筛线判断。学校缺失须先要求使用者补齐；任何硬门槛待核验或不通过均不输出维度分、部分分或总分。学校匹配成功不能抵消专升本或已确认独立学院门槛。

## 维护与核验

不在每次筛选时联网重建名单。疑似榜单录入错误须回溯同一2025官方来源、记录修正并跑测试；仅收到用户明确更新榜单年份的请求时换版。

```bash
python3 -m unittest discover -s scripts -p 'test_school_lookup.py' -v
```

## Change Log

| 日期 | 变更 |
|---|---|
| 2026-10-07 | 对齐1.8.0六项硬门槛及缺项完全不评分规则，榜单数据未变。 |
| 2026-10-07 | 固化2025口径；新增国内589所主榜及QS前200条离线表，保留并列及来源限制，加入精确匹配和HR分流规则。 |
