# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workbench.visual.spec.ts >> workbench management uses left navigation, full results, and right tools
- Location: tests\visual\workbench.visual.spec.ts:223:1

# Error details

```
Error: expect(page).toHaveScreenshot(expected) failed

  76372 pixels (ratio 0.04 of all image pixels) are different.

  Snapshot: workbench-management-overview.png

Call log:
  - Expect "toHaveScreenshot(workbench-management-overview.png)" with timeout 5000ms
    - verifying given screenshot expectation
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - 76372 pixels (ratio 0.04 of all image pixels) are different.
  - waiting 100ms before taking screenshot
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - captured a stable screenshot
  - 76372 pixels (ratio 0.04 of all image pixels) are different.

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - banner [ref=e5]:
    - link "JR Jig Record 回首頁" [ref=e7] [cursor=pointer]:
      - /url: /search
      - generic [ref=e8]: JR
      - generic [ref=e9]:
        - strong [ref=e10]: Jig Record
        - generic [ref=e11]: 回首頁
    - generic [ref=e12]:
      - button "治具收/退料" [ref=e13] [cursor=pointer]
      - button "匯出中心" [ref=e14] [cursor=pointer]
      - button "Workspace UI 教學" [ref=e15] [cursor=pointer]
    - region "UI 介面" [ref=e17]:
      - tablist "切換 Workspace 或 Form UI" [ref=e19]:
        - tab [selected] [ref=e20] [cursor=pointer]:
          - strong [ref=e21]: Workspace UI
        - tab [ref=e22] [cursor=pointer]:
          - strong [ref=e23]: Form UI
      - generic [ref=e26]:
        - generic [ref=e27]: 預設
        - combobox "登入後預設介面" [ref=e28] [cursor=pointer]:
          - option "Workspace UI" [selected]
          - option "Form UI"
    - generic [ref=e29]:
      - generic [ref=e30]:
        - generic [ref=e31]: 視覺測試管理員
        - button "今日收料 32" [ref=e33] [cursor=pointer]:
          - generic [ref=e34]: 今日收料
          - strong [ref=e35]: "32"
        - button "今日退料 8" [ref=e37] [cursor=pointer]:
          - generic [ref=e38]: 今日退料
          - strong [ref=e39]: "8"
        - button "低水位 2" [ref=e41] [cursor=pointer]:
          - generic [ref=e42]: 低水位
          - strong [ref=e43]: "2"
      - generic [ref=e44]:
        - combobox "選擇客戶" [ref=e46]:
          - option "VISUAL - Visual Regression Customer" [selected]
        - button "更多" [ref=e48] [cursor=pointer]
        - button "登出" [ref=e49] [cursor=pointer]
  - main [ref=e50]:
    - region "Workspace UI 系統介面" [ref=e51]:
      - region "現場工作台收退料總檢視" [ref=e52]:
        - generic [ref=e53]:
          - complementary "現場工作台總檢視導覽" [ref=e54]:
            - generic [ref=e56]:
              - generic [ref=e57]: 現場工作台
              - heading "收退料總檢視" [level=2] [ref=e58]
            - tablist "工作台作業模式" [ref=e59]:
              - tab "收料／退料" [ref=e60] [cursor=pointer]
              - tab "查詢治具" [ref=e61] [cursor=pointer]
              - tab "查詢機種" [ref=e62] [cursor=pointer]
              - tab "收／退料總檢視" [selected] [ref=e63] [cursor=pointer]
          - main [ref=e64]:
            - generic [ref=e65]:
              - generic [ref=e66]:
                - generic [ref=e67]: 庫存作業
                - heading "收退料總檢視" [level=2] [ref=e68]
              - generic [ref=e69]: VISUAL
            - region "收退料總檢視結果表格" [ref=e74]:
              - generic [ref=e75]:
                - generic [ref=e76]:
                  - strong [ref=e77]: "60"
                  - generic [ref=e78]: 筆資料
                - generic [ref=e79]:
                  - button "匯出篩選結果" [ref=e80] [cursor=pointer]
                  - generic [ref=e81]:
                    - text: 每頁
                    - combobox "每頁" [ref=e82]:
                      - option "50" [selected]
                      - option "100"
              - table [ref=e84]:
                - rowgroup [ref=e85]:
                  - row [ref=e86]:
                    - columnheader "類型" [ref=e87]
                    - columnheader "單號" [ref=e88]
                    - columnheader "治具編號" [ref=e89]
                    - columnheader "來源" [ref=e90]
                    - columnheader "datecode/編號" [ref=e91]
                    - columnheader "數量" [ref=e92]
                    - columnheader "操作人員" [ref=e93]
                    - columnheader "日期" [ref=e94]
                    - columnheader "備註" [ref=e95]
                - rowgroup [ref=e96]:
                  - row [ref=e97]:
                    - cell "退料" [ref=e98]
                    - cell "VIS-0001" [ref=e100]
                    - cell "FX-001" [ref=e101]
                    - cell "自購" [ref=e102]
                    - cell "2200" [ref=e103]
                    - cell "1" [ref=e104]
                    - cell "Operator A" [ref=e105]
                    - cell "2026-08-25" [ref=e106]
                    - cell [ref=e107]:
                      - button "Visual regression fixtur…" [ref=e108] [cursor=pointer]
                  - row [ref=e109]:
                    - cell "收料" [ref=e110]
                    - cell "VIS-0002" [ref=e112]
                    - cell "FX-002" [ref=e113]
                    - cell "客供" [ref=e114]
                    - cell "2201" [ref=e115]
                    - cell "2" [ref=e116]
                    - cell "Operator B" [ref=e117]
                    - cell "2026-08-24" [ref=e118]
                    - cell "-" [ref=e119]
                  - row [ref=e120]:
                    - cell "收料" [ref=e121]
                    - cell "VIS-0003" [ref=e123]
                    - cell "FX-003" [ref=e124]
                    - cell "客供" [ref=e125]
                    - cell "2202" [ref=e126]
                    - cell "3" [ref=e127]
                    - cell "Operator A" [ref=e128]
                    - cell "2026-08-23" [ref=e129]
                    - cell "-" [ref=e130]
                  - row [ref=e131]:
                    - cell "收料" [ref=e132]
                    - cell "VIS-0004" [ref=e134]
                    - cell "FX-004" [ref=e135]
                    - cell "自購" [ref=e136]
                    - cell "2203" [ref=e137]
                    - cell "4" [ref=e138]
                    - cell "Operator B" [ref=e139]
                    - cell "2026-08-22" [ref=e140]
                    - cell "-" [ref=e141]
                  - row [ref=e142]:
                    - cell "退料" [ref=e143]
                    - cell "VIS-0005" [ref=e145]
                    - cell "FX-005" [ref=e146]
                    - cell "客供" [ref=e147]
                    - cell "2204" [ref=e148]
                    - cell "5" [ref=e149]
                    - cell "Operator A" [ref=e150]
                    - cell "2026-08-21" [ref=e151]
                    - cell "-" [ref=e152]
                  - row [ref=e153]:
                    - cell "收料" [ref=e154]
                    - cell "VIS-0006" [ref=e156]
                    - cell "FX-006" [ref=e157]
                    - cell "客供" [ref=e158]
                    - cell "2205" [ref=e159]
                    - cell "6" [ref=e160]
                    - cell "Operator B" [ref=e161]
                    - cell "2026-08-25" [ref=e162]
                    - cell "-" [ref=e163]
                  - row [ref=e164]:
                    - cell "收料" [ref=e165]
                    - cell "VIS-0007" [ref=e167]
                    - cell "FX-007" [ref=e168]
                    - cell "自購" [ref=e169]
                    - cell "2206" [ref=e170]
                    - cell "7" [ref=e171]
                    - cell "Operator A" [ref=e172]
                    - cell "2026-08-24" [ref=e173]
                    - cell "-" [ref=e174]
                  - row [ref=e175]:
                    - cell "收料" [ref=e176]
                    - cell "VIS-0008" [ref=e178]
                    - cell "FX-008" [ref=e179]
                    - cell "客供" [ref=e180]
                    - cell "2207" [ref=e181]
                    - cell "8" [ref=e182]
                    - cell "Operator B" [ref=e183]
                    - cell "2026-08-23" [ref=e184]
                    - cell "-" [ref=e185]
                  - row [ref=e186]:
                    - cell "退料" [ref=e187]
                    - cell "VIS-0009" [ref=e189]
                    - cell "FX-001" [ref=e190]
                    - cell "客供" [ref=e191]
                    - cell "2208" [ref=e192]
                    - cell "9" [ref=e193]
                    - cell "Operator A" [ref=e194]
                    - cell "2026-08-22" [ref=e195]
                    - cell "-" [ref=e196]
                  - row [ref=e197]:
                    - cell "收料" [ref=e198]
                    - cell "VIS-0010" [ref=e200]
                    - cell "FX-002" [ref=e201]
                    - cell "自購" [ref=e202]
                    - cell "2209" [ref=e203]
                    - cell "1" [ref=e204]
                    - cell "Operator B" [ref=e205]
                    - cell "2026-08-21" [ref=e206]
                    - cell "-" [ref=e207]
                  - row [ref=e208]:
                    - cell "收料" [ref=e209]
                    - cell "VIS-0011" [ref=e211]
                    - cell "FX-003" [ref=e212]
                    - cell "客供" [ref=e213]
                    - cell "2210" [ref=e214]
                    - cell "2" [ref=e215]
                    - cell "Operator A" [ref=e216]
                    - cell "2026-08-25" [ref=e217]
                    - cell "-" [ref=e218]
                  - row [ref=e219]:
                    - cell "收料" [ref=e220]
                    - cell "VIS-0012" [ref=e222]
                    - cell "FX-004" [ref=e223]
                    - cell "客供" [ref=e224]
                    - cell "2211" [ref=e225]
                    - cell "3" [ref=e226]
                    - cell "Operator B" [ref=e227]
                    - cell "2026-08-24" [ref=e228]
                    - cell "-" [ref=e229]
                  - row [ref=e230]:
                    - cell "退料" [ref=e231]
                    - cell "VIS-0013" [ref=e233]
                    - cell "FX-005" [ref=e234]
                    - cell "自購" [ref=e235]
                    - cell "2212" [ref=e236]
                    - cell "4" [ref=e237]
                    - cell "Operator A" [ref=e238]
                    - cell "2026-08-23" [ref=e239]
                    - cell "-" [ref=e240]
                  - row [ref=e241]:
                    - cell "收料" [ref=e242]
                    - cell "VIS-0014" [ref=e244]
                    - cell "FX-006" [ref=e245]
                    - cell "客供" [ref=e246]
                    - cell "2213" [ref=e247]
                    - cell "5" [ref=e248]
                    - cell "Operator B" [ref=e249]
                    - cell "2026-08-22" [ref=e250]
                    - cell "-" [ref=e251]
                  - row [ref=e252]:
                    - cell "收料" [ref=e253]
                    - cell "VIS-0015" [ref=e255]
                    - cell "FX-007" [ref=e256]
                    - cell "客供" [ref=e257]
                    - cell "2214" [ref=e258]
                    - cell "6" [ref=e259]
                    - cell "Operator A" [ref=e260]
                    - cell "2026-08-21" [ref=e261]
                    - cell "-" [ref=e262]
                  - row [ref=e263]:
                    - cell "收料" [ref=e264]
                    - cell "VIS-0016" [ref=e266]
                    - cell "FX-008" [ref=e267]
                    - cell "自購" [ref=e268]
                    - cell "2215" [ref=e269]
                    - cell "7" [ref=e270]
                    - cell "Operator B" [ref=e271]
                    - cell "2026-08-25" [ref=e272]
                    - cell "-" [ref=e273]
                  - row [ref=e274]:
                    - cell "退料" [ref=e275]
                    - cell "VIS-0017" [ref=e277]
                    - cell "FX-001" [ref=e278]
                    - cell "客供" [ref=e279]
                    - cell "2216" [ref=e280]
                    - cell "8" [ref=e281]
                    - cell "Operator A" [ref=e282]
                    - cell "2026-08-24" [ref=e283]
                    - cell "-" [ref=e284]
                  - row [ref=e285]:
                    - cell "收料" [ref=e286]
                    - cell "VIS-0018" [ref=e288]
                    - cell "FX-002" [ref=e289]
                    - cell "客供" [ref=e290]
                    - cell "2217" [ref=e291]
                    - cell "9" [ref=e292]
                    - cell "Operator B" [ref=e293]
                    - cell "2026-08-23" [ref=e294]
                    - cell "-" [ref=e295]
                  - row [ref=e296]:
                    - cell "收料" [ref=e297]
                    - cell "VIS-0019" [ref=e299]
                    - cell "FX-003" [ref=e300]
                    - cell "自購" [ref=e301]
                    - cell "2218" [ref=e302]
                    - cell "1" [ref=e303]
                    - cell "Operator A" [ref=e304]
                    - cell "2026-08-22" [ref=e305]
                    - cell "-" [ref=e306]
                  - row [ref=e307]:
                    - cell "收料" [ref=e308]
                    - cell "VIS-0020" [ref=e310]
                    - cell "FX-004" [ref=e311]
                    - cell "客供" [ref=e312]
                    - cell "2219" [ref=e313]
                    - cell "2" [ref=e314]
                    - cell "Operator B" [ref=e315]
                    - cell "2026-08-21" [ref=e316]
                    - cell "-" [ref=e317]
                  - row [ref=e318]:
                    - cell "退料" [ref=e319]
                    - cell "VIS-0021" [ref=e321]
                    - cell "FX-005" [ref=e322]
                    - cell "客供" [ref=e323]
                    - cell "2220" [ref=e324]
                    - cell "3" [ref=e325]
                    - cell "Operator A" [ref=e326]
                    - cell "2026-08-25" [ref=e327]
                    - cell "-" [ref=e328]
                  - row [ref=e329]:
                    - cell "收料" [ref=e330]
                    - cell "VIS-0022" [ref=e332]
                    - cell "FX-006" [ref=e333]
                    - cell "自購" [ref=e334]
                    - cell "2221" [ref=e335]
                    - cell "4" [ref=e336]
                    - cell "Operator B" [ref=e337]
                    - cell "2026-08-24" [ref=e338]
                    - cell "-" [ref=e339]
                  - row [ref=e340]:
                    - cell "收料" [ref=e341]
                    - cell "VIS-0023" [ref=e343]
                    - cell "FX-007" [ref=e344]
                    - cell "客供" [ref=e345]
                    - cell "2222" [ref=e346]
                    - cell "5" [ref=e347]
                    - cell "Operator A" [ref=e348]
                    - cell "2026-08-23" [ref=e349]
                    - cell "-" [ref=e350]
                  - row [ref=e351]:
                    - cell "收料" [ref=e352]
                    - cell "VIS-0024" [ref=e354]
                    - cell "FX-008" [ref=e355]
                    - cell "客供" [ref=e356]
                    - cell "2223" [ref=e357]
                    - cell "6" [ref=e358]
                    - cell "Operator B" [ref=e359]
                    - cell "2026-08-22" [ref=e360]
                    - cell "-" [ref=e361]
                  - row [ref=e362]:
                    - cell "退料" [ref=e363]
                    - cell "VIS-0025" [ref=e365]
                    - cell "FX-001" [ref=e366]
                    - cell "自購" [ref=e367]
                    - cell "2224" [ref=e368]
                    - cell "7" [ref=e369]
                    - cell "Operator A" [ref=e370]
                    - cell "2026-08-21" [ref=e371]
                    - cell "-" [ref=e372]
                  - row [ref=e373]:
                    - cell "收料" [ref=e374]
                    - cell "VIS-0026" [ref=e376]
                    - cell "FX-002" [ref=e377]
                    - cell "客供" [ref=e378]
                    - cell "2225" [ref=e379]
                    - cell "8" [ref=e380]
                    - cell "Operator B" [ref=e381]
                    - cell "2026-08-25" [ref=e382]
                    - cell "-" [ref=e383]
                  - row [ref=e384]:
                    - cell "收料" [ref=e385]
                    - cell "VIS-0027" [ref=e387]
                    - cell "FX-003" [ref=e388]
                    - cell "客供" [ref=e389]
                    - cell "2226" [ref=e390]
                    - cell "9" [ref=e391]
                    - cell "Operator A" [ref=e392]
                    - cell "2026-08-24" [ref=e393]
                    - cell "-" [ref=e394]
                  - row [ref=e395]:
                    - cell "收料" [ref=e396]
                    - cell "VIS-0028" [ref=e398]
                    - cell "FX-004" [ref=e399]
                    - cell "自購" [ref=e400]
                    - cell "2227" [ref=e401]
                    - cell "1" [ref=e402]
                    - cell "Operator B" [ref=e403]
                    - cell "2026-08-23" [ref=e404]
                    - cell "-" [ref=e405]
                  - row [ref=e406]:
                    - cell "退料" [ref=e407]
                    - cell "VIS-0029" [ref=e409]
                    - cell "FX-005" [ref=e410]
                    - cell "客供" [ref=e411]
                    - cell "2228" [ref=e412]
                    - cell "2" [ref=e413]
                    - cell "Operator A" [ref=e414]
                    - cell "2026-08-22" [ref=e415]
                    - cell "-" [ref=e416]
                  - row [ref=e417]:
                    - cell "收料" [ref=e418]
                    - cell "VIS-0030" [ref=e420]
                    - cell "FX-006" [ref=e421]
                    - cell "客供" [ref=e422]
                    - cell "2229" [ref=e423]
                    - cell "3" [ref=e424]
                    - cell "Operator B" [ref=e425]
                    - cell "2026-08-21" [ref=e426]
                    - cell "-" [ref=e427]
                  - row [ref=e428]:
                    - cell "收料" [ref=e429]
                    - cell "VIS-0031" [ref=e431]
                    - cell "FX-007" [ref=e432]
                    - cell "自購" [ref=e433]
                    - cell "2230" [ref=e434]
                    - cell "4" [ref=e435]
                    - cell "Operator A" [ref=e436]
                    - cell "2026-08-25" [ref=e437]
                    - cell "-" [ref=e438]
                  - row [ref=e439]:
                    - cell "收料" [ref=e440]
                    - cell "VIS-0032" [ref=e442]
                    - cell "FX-008" [ref=e443]
                    - cell "客供" [ref=e444]
                    - cell "2231" [ref=e445]
                    - cell "5" [ref=e446]
                    - cell "Operator B" [ref=e447]
                    - cell "2026-08-24" [ref=e448]
                    - cell "-" [ref=e449]
                  - row [ref=e450]:
                    - cell "退料" [ref=e451]
                    - cell "VIS-0033" [ref=e453]
                    - cell "FX-001" [ref=e454]
                    - cell "客供" [ref=e455]
                    - cell "2232" [ref=e456]
                    - cell "6" [ref=e457]
                    - cell "Operator A" [ref=e458]
                    - cell "2026-08-23" [ref=e459]
                    - cell "-" [ref=e460]
                  - row [ref=e461]:
                    - cell "收料" [ref=e462]
                    - cell "VIS-0034" [ref=e464]
                    - cell "FX-002" [ref=e465]
                    - cell "自購" [ref=e466]
                    - cell "2233" [ref=e467]
                    - cell "7" [ref=e468]
                    - cell "Operator B" [ref=e469]
                    - cell "2026-08-22" [ref=e470]
                    - cell "-" [ref=e471]
                  - row [ref=e472]:
                    - cell "收料" [ref=e473]
                    - cell "VIS-0035" [ref=e475]
                    - cell "FX-003" [ref=e476]
                    - cell "客供" [ref=e477]
                    - cell "2234" [ref=e478]
                    - cell "8" [ref=e479]
                    - cell "Operator A" [ref=e480]
                    - cell "2026-08-21" [ref=e481]
                    - cell "-" [ref=e482]
                  - row [ref=e483]:
                    - cell "收料" [ref=e484]
                    - cell "VIS-0036" [ref=e486]
                    - cell "FX-004" [ref=e487]
                    - cell "客供" [ref=e488]
                    - cell "2235" [ref=e489]
                    - cell "9" [ref=e490]
                    - cell "Operator B" [ref=e491]
                    - cell "2026-08-25" [ref=e492]
                    - cell "-" [ref=e493]
                  - row [ref=e494]:
                    - cell "退料" [ref=e495]
                    - cell "VIS-0037" [ref=e497]
                    - cell "FX-005" [ref=e498]
                    - cell "自購" [ref=e499]
                    - cell "2236" [ref=e500]
                    - cell "1" [ref=e501]
                    - cell "Operator A" [ref=e502]
                    - cell "2026-08-24" [ref=e503]
                    - cell "-" [ref=e504]
                  - row [ref=e505]:
                    - cell "收料" [ref=e506]
                    - cell "VIS-0038" [ref=e508]
                    - cell "FX-006" [ref=e509]
                    - cell "客供" [ref=e510]
                    - cell "2237" [ref=e511]
                    - cell "2" [ref=e512]
                    - cell "Operator B" [ref=e513]
                    - cell "2026-08-23" [ref=e514]
                    - cell "-" [ref=e515]
                  - row [ref=e516]:
                    - cell "收料" [ref=e517]
                    - cell "VIS-0039" [ref=e519]
                    - cell "FX-007" [ref=e520]
                    - cell "客供" [ref=e521]
                    - cell "2238" [ref=e522]
                    - cell "3" [ref=e523]
                    - cell "Operator A" [ref=e524]
                    - cell "2026-08-22" [ref=e525]
                    - cell "-" [ref=e526]
                  - row [ref=e527]:
                    - cell "收料" [ref=e528]
                    - cell "VIS-0040" [ref=e530]
                    - cell "FX-008" [ref=e531]
                    - cell "自購" [ref=e532]
                    - cell "2239" [ref=e533]
                    - cell "4" [ref=e534]
                    - cell "Operator B" [ref=e535]
                    - cell "2026-08-21" [ref=e536]
                    - cell "-" [ref=e537]
                  - row [ref=e538]:
                    - cell "退料" [ref=e539]
                    - cell "VIS-0041" [ref=e541]
                    - cell "FX-001" [ref=e542]
                    - cell "客供" [ref=e543]
                    - cell "2240" [ref=e544]
                    - cell "5" [ref=e545]
                    - cell "Operator A" [ref=e546]
                    - cell "2026-08-25" [ref=e547]
                    - cell "-" [ref=e548]
                  - row [ref=e549]:
                    - cell "收料" [ref=e550]
                    - cell "VIS-0042" [ref=e552]
                    - cell "FX-002" [ref=e553]
                    - cell "客供" [ref=e554]
                    - cell "2241" [ref=e555]
                    - cell "6" [ref=e556]
                    - cell "Operator B" [ref=e557]
                    - cell "2026-08-24" [ref=e558]
                    - cell "-" [ref=e559]
                  - row [ref=e560]:
                    - cell "收料" [ref=e561]
                    - cell "VIS-0043" [ref=e563]
                    - cell "FX-003" [ref=e564]
                    - cell "自購" [ref=e565]
                    - cell "2242" [ref=e566]
                    - cell "7" [ref=e567]
                    - cell "Operator A" [ref=e568]
                    - cell "2026-08-23" [ref=e569]
                    - cell "-" [ref=e570]
                  - row [ref=e571]:
                    - cell "收料" [ref=e572]
                    - cell "VIS-0044" [ref=e574]
                    - cell "FX-004" [ref=e575]
                    - cell "客供" [ref=e576]
                    - cell "2243" [ref=e577]
                    - cell "8" [ref=e578]
                    - cell "Operator B" [ref=e579]
                    - cell "2026-08-22" [ref=e580]
                    - cell "-" [ref=e581]
                  - row [ref=e582]:
                    - cell "退料" [ref=e583]
                    - cell "VIS-0045" [ref=e585]
                    - cell "FX-005" [ref=e586]
                    - cell "客供" [ref=e587]
                    - cell "2244" [ref=e588]
                    - cell "9" [ref=e589]
                    - cell "Operator A" [ref=e590]
                    - cell "2026-08-21" [ref=e591]
                    - cell "-" [ref=e592]
                  - row [ref=e593]:
                    - cell "收料" [ref=e594]
                    - cell "VIS-0046" [ref=e596]
                    - cell "FX-006" [ref=e597]
                    - cell "自購" [ref=e598]
                    - cell "2245" [ref=e599]
                    - cell "1" [ref=e600]
                    - cell "Operator B" [ref=e601]
                    - cell "2026-08-25" [ref=e602]
                    - cell "-" [ref=e603]
                  - row [ref=e604]:
                    - cell "收料" [ref=e605]
                    - cell "VIS-0047" [ref=e607]
                    - cell "FX-007" [ref=e608]
                    - cell "客供" [ref=e609]
                    - cell "2246" [ref=e610]
                    - cell "2" [ref=e611]
                    - cell "Operator A" [ref=e612]
                    - cell "2026-08-24" [ref=e613]
                    - cell "-" [ref=e614]
                  - row [ref=e615]:
                    - cell "收料" [ref=e616]
                    - cell "VIS-0048" [ref=e618]
                    - cell "FX-008" [ref=e619]
                    - cell "客供" [ref=e620]
                    - cell "2247" [ref=e621]
                    - cell "3" [ref=e622]
                    - cell "Operator B" [ref=e623]
                    - cell "2026-08-23" [ref=e624]
                    - cell "-" [ref=e625]
                  - row [ref=e626]:
                    - cell "退料" [ref=e627]
                    - cell "VIS-0049" [ref=e629]
                    - cell "FX-001" [ref=e630]
                    - cell "自購" [ref=e631]
                    - cell "2248" [ref=e632]
                    - cell "4" [ref=e633]
                    - cell "Operator A" [ref=e634]
                    - cell "2026-08-22" [ref=e635]
                    - cell "-" [ref=e636]
                  - row [ref=e637]:
                    - cell "收料" [ref=e638]
                    - cell "VIS-0050" [ref=e640]
                    - cell "FX-002" [ref=e641]
                    - cell "客供" [ref=e642]
                    - cell "2249" [ref=e643]
                    - cell "5" [ref=e644]
                    - cell "Operator B" [ref=e645]
                    - cell "2026-08-21" [ref=e646]
                    - cell "-" [ref=e647]
              - generic [ref=e648]:
                - button "上一頁" [disabled] [ref=e649]
                - generic [ref=e650]: 第 1 / 2 頁
                - button "下一頁" [ref=e651] [cursor=pointer]
          - complementary "工作台篩選與編輯工具" [ref=e652]:
            - generic [ref=e653]:
              - generic [ref=e654]:
                - generic [ref=e655]: 操作面板
                - heading "篩選條件" [level=2] [ref=e656]
              - button "收合篩選" [expanded] [ref=e657] [cursor=pointer]
            - region "收退料總檢視條件" [ref=e659]:
              - generic [ref=e660]:
                - generic [ref=e661]:
                  - strong [ref=e662]: 篩選條件
                  - generic [ref=e663]: 收退料總檢視｜依目前功能顯示適用欄位
                - generic [ref=e664]:
                  - button "重新整理" [ref=e665]
                  - button "重設" [ref=e666] [cursor=pointer]
                  - button "套用條件" [ref=e667] [cursor=pointer]
              - generic [ref=e668]:
                - generic [ref=e669]:
                  - generic [ref=e670]: 類型
                  - group "類型複選" [ref=e671]:
                    - generic "全部類型" [ref=e672] [cursor=pointer]
                - generic [ref=e676]:
                  - generic [ref=e677]: 來源
                  - group "來源複選" [ref=e678]:
                    - generic "全部來源" [ref=e679] [cursor=pointer]
                - generic [ref=e683]:
                  - generic [ref=e684]: 起始日期
                  - textbox "起始日期" [ref=e685]
                - generic [ref=e686]:
                  - generic [ref=e687]: 結束日期
                  - textbox "結束日期" [ref=e688]
                - generic [ref=e689]:
                  - generic [ref=e690]: 治具編號
                  - textbox "治具編號" [ref=e691]:
                    - /placeholder: 治具編號 / 名稱
                - generic [ref=e692]:
                  - generic [ref=e693]: 單號
                  - textbox "單號" [ref=e694]
                - generic [ref=e695]:
                  - generic [ref=e696]: datecode/編號
                  - textbox "datecode/編號" [ref=e697]
                - generic [ref=e698]:
                  - generic [ref=e699]: 操作人員
                  - textbox "操作人員" [ref=e700]
```

# Test source

```ts
  146 |         identifier_rows: [{ fixture_id: fixtures[0]!.id, identifier: "2204", stock_qty: 12, customer_supplied_qty: 7, self_purchased_qty: 5 }],
  147 |         related_models: [],
  148 |         station_rows: [],
  149 |         transactions: []
  150 |       });
  151 |     }
  152 |     if (url.pathname.endsWith("/inventory/transactions/overview")) {
  153 |       const pageNumber = Number(url.searchParams.get("page") ?? "1");
  154 |       const pageSize = Number(url.searchParams.get("page_size") ?? "50");
  155 |       const start = (pageNumber - 1) * pageSize;
  156 |       return fulfillJson(route, {
  157 |         items: transactionRows.slice(start, start + pageSize),
  158 |         page: pageNumber,
  159 |         page_size: pageSize,
  160 |         total: transactionRows.length
  161 |       });
  162 |     }
  163 |     if (url.pathname.endsWith("/inventory/admin/transactions")) {
  164 |       return fulfillJson(route, { items: ledgerRows, page: 1, page_size: 12, total: ledgerRows.length });
  165 |     }
  166 |     if (url.pathname.endsWith("/inventory/dashboard-summary")) {
  167 |       return fulfillJson(route, {
  168 |         today_receipt_qty: 32,
  169 |         today_return_qty: 8,
  170 |         low_stock_count: 2,
  171 |         low_stock_preview_entries: [],
  172 |         has_more_low_stock_entries: false,
  173 |         recent_receipt_entries: [],
  174 |         recent_return_entries: []
  175 |       });
  176 |     }
  177 |     return fulfillJson(route, []);
  178 |   });
  179 | }
  180 | 
  181 | test("workbench combined transaction overview matches the approved responsive baseline", async ({ page }, testInfo) => {
  182 |   await installDeterministicApi(page);
  183 |   await page.goto("/search?ui_surface=workbench&workbench_mode=transaction&transaction_type=receipt&customer=1");
  184 |   await page.locator(".workbench-ui").waitFor();
  185 |   await expect(page.locator('.workbench-mode-tabs [role="tab"]')).toHaveCount(4);
  186 |   await expect(page.locator('.workbench-mode-tabs [role="tab"]').last()).toHaveText("管理後臺");
  187 |   await expect(page.locator(".workbench-recent-table tbody tr")).toHaveCount(50);
  188 |   await expect(page.locator(".workbench-table-pager")).toContainText("第 1 / 2 頁");
  189 | 
  190 |   const horizontalOverflow = await page.evaluate(() =>
  191 |     Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  192 |   );
  193 |   expect(horizontalOverflow, `${testInfo.project.name} must not overflow the page horizontally`).toBeLessThanOrEqual(1);
  194 | 
  195 |   await expect(page).toHaveScreenshot("workbench-receipt.png", { fullPage: false });
  196 | 
  197 |   await page.getByRole("tab", { name: "管理後臺", exact: true }).click();
  198 |   await expect(page.locator('[data-tour="workbench-management-launcher"]')).toBeVisible();
  199 |   await expect(page.locator('[data-tour="workbench-management-launcher"]')).toContainText("匯出中心");
  200 |   const managementOverflow = await page.evaluate(() =>
  201 |     Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  202 |   );
  203 |   expect(managementOverflow, `${testInfo.project.name} management launcher must not overflow horizontally`).toBeLessThanOrEqual(1);
  204 | });
  205 | 
  206 | test("workbench keeps fixture and identifier lookup as explicit URL-backed modes", async ({ page }, testInfo) => {
  207 |   await installDeterministicApi(page);
  208 |   await page.goto("/search?ui_surface=workbench&workbench_mode=fixture&fixture_search=identifier&q=2204&selected_id=101&customer=1");
  209 |   await page.locator(".workbench-ui").waitFor();
  210 |   await expect(page.getByRole("button", { name: "Datecode／序號", exact: true })).toHaveAttribute("aria-pressed", "true");
  211 |   await expect(page.locator(".workbench-query-form input")).toHaveValue("2204");
  212 |   await expect(page.locator(".workbench-results")).toContainText("2204");
  213 |   await expect(page.locator(".workbench-detail")).toContainText("FX-001");
  214 |   await expect(page.locator(".toast-card.error")).toHaveCount(0);
  215 | 
  216 |   const horizontalOverflow = await page.evaluate(() =>
  217 |     Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  218 |   );
  219 |   expect(horizontalOverflow, `${testInfo.project.name} identifier search must not overflow horizontally`).toBeLessThanOrEqual(1);
  220 |   await expect(page).toHaveScreenshot("workbench-identifier-search.png", { fullPage: false });
  221 | });
  222 | 
  223 | test("workbench management uses left navigation, full results, and right tools", async ({ page }, testInfo) => {
  224 |   await installDeterministicApi(page, "admin");
  225 |   await page.goto("/inventory/overview?ui_surface=workbench&customer=1");
  226 |   await page.locator(".workbench-management-ui").waitFor();
  227 |   await expect(page.locator(".workbench-management-columns > .workbench-panel")).toHaveCount(3);
  228 |   await expect(page.locator(".workbench-management-detail")).toContainText("篩選條件");
  229 |   await expect(page.locator(".workbench-management-detail")).not.toContainText("操作角色");
  230 |   await expect(page.locator(".workbench-management-results .filter-panel")).toHaveCount(0);
  231 | 
  232 |   const layout = await page.evaluate(() => {
  233 |     const panels = Array.from(document.querySelectorAll<HTMLElement>(".workbench-management-columns > .workbench-panel"));
  234 |     return {
  235 |       lefts: panels.map((panel) => Math.round(panel.getBoundingClientRect().left)),
  236 |       widths: panels.map((panel) => Math.round(panel.getBoundingClientRect().width)),
  237 |       overflow: Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth)
  238 |     };
  239 |   });
  240 |   expect(layout.lefts[0], `${testInfo.project.name} navigation should be first`).toBeLessThan(layout.lefts[1]!);
  241 |   expect(layout.lefts[1], `${testInfo.project.name} results should be centered`).toBeLessThan(layout.lefts[2]!);
  242 |   expect(layout.widths[1], `${testInfo.project.name} result panel should receive the most width`).toBeGreaterThan(layout.widths[2]!);
  243 |   expect(layout.widths[2], `${testInfo.project.name} tool panel must remain usable`).toBeGreaterThanOrEqual(250);
  244 |   expect(layout.overflow, `${testInfo.project.name} management page must not overflow horizontally`).toBeLessThanOrEqual(1);
  245 | 
> 246 |   await expect(page).toHaveScreenshot("workbench-management-overview.png", { fullPage: false });
      |                      ^ Error: expect(page).toHaveScreenshot(expected) failed
  247 | });
  248 | 
  249 | test("workbench image maintenance uses a selected list row and right inspector", async ({ page }, testInfo) => {
  250 |   await installDeterministicApi(page, "admin");
  251 |   await page.goto("/master/images?ui_surface=workbench&customer=1");
  252 |   await page.locator(".workbench-management-ui").waitFor();
  253 |   await expect(page.locator("tbody tr.workbench-image-row")).toHaveCount(fixtures.length);
  254 |   await expect(page.locator("tbody tr.workbench-image-row.selected")).toHaveCount(1);
  255 |   await expect(page.locator(".workbench-management-detail")).toContainText("SELECTED FIXTURE");
  256 |   await expect(page.locator(".workbench-management-detail")).toContainText("尚無圖片");
  257 |   await expect(page.locator(".workbench-management-results thead th")).toHaveCount(4);
  258 |   await page.locator(".workbench-filter-toggle").click();
  259 |   await expect(page.locator(".workbench-management-detail .form-image-filters")).toBeHidden();
  260 |   await expect(page.locator(".workbench-filter-toggle")).toHaveAttribute("aria-expanded", "false");
  261 |   await page.locator(".workbench-filter-toggle").click();
  262 | 
  263 |   const overflow = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth));
  264 |   expect(overflow, `${testInfo.project.name} image maintenance must not overflow horizontally`).toBeLessThanOrEqual(1);
  265 |   await expect(page).toHaveScreenshot("workbench-image-maintenance.png", { fullPage: false });
  266 | });
  267 | 
  268 | test("workbench ledger keeps the case list central and details in right tools", async ({ page }, testInfo) => {
  269 |   await installDeterministicApi(page, "admin");
  270 |   await page.goto("/master/ledger?ui_surface=workbench&customer=1");
  271 |   await page.locator(".workbench-management-ui").waitFor();
  272 |   await expect(page.locator(".workbench-management-results .workbench-ledger-table tbody tr")).toHaveCount(ledgerRows.length);
  273 |   await expect(page.locator(".workbench-management-results .workbench-ledger-detail")).toHaveCount(0);
  274 |   await expect(page.locator(".workbench-management-detail .workbench-ledger-side")).toContainText("LED-0001");
  275 |   await expect(page.locator(".workbench-management-detail .workbench-ledger-item-list > article")).toHaveCount(1);
  276 | 
  277 |   const typeSelect = page.locator('.workbench-management-detail details[aria-label="作業類型複選"]');
  278 |   await typeSelect.locator("summary").click();
  279 |   await expect(typeSelect.locator(".ui-multi-select-option")).toHaveCount(2);
  280 |   await expect(typeSelect.locator('.ui-multi-select-option input[type="checkbox"]').first()).toHaveCSS("clip-path", "inset(50%)");
  281 |   await expect(page).toHaveScreenshot("workbench-ledger-multiselect-open.png", { fullPage: false });
  282 |   await typeSelect.locator("summary").click();
  283 | 
  284 |   const overflow = await page.evaluate(() => Math.max(0, document.documentElement.scrollWidth - document.documentElement.clientWidth));
  285 |   expect(overflow, `${testInfo.project.name} ledger must not overflow horizontally`).toBeLessThanOrEqual(1);
  286 |   await expect(page).toHaveScreenshot("workbench-ledger-management.png", { fullPage: false });
  287 | 
  288 |   await page.locator(".workbench-filter-toggle").click();
  289 |   await expect(page.locator(".workbench-management-detail .workbench-admin-filter-grid")).toBeHidden();
  290 |   await expect(page.locator(".workbench-management-detail .workbench-ledger-side")).toBeVisible();
  291 |   await expect(page).toHaveScreenshot("workbench-ledger-management-collapsed.png", { fullPage: false });
  292 | });
  293 | 
```