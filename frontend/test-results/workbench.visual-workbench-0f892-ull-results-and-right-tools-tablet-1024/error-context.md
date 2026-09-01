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

  54704 pixels (ratio 0.06 of all image pixels) are different.

  Snapshot: workbench-management-overview.png

Call log:
  - Expect "toHaveScreenshot(workbench-management-overview.png)" with timeout 5000ms
    - verifying given screenshot expectation
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - 54704 pixels (ratio 0.06 of all image pixels) are different.
  - waiting 100ms before taking screenshot
  - taking page screenshot
    - disabled all CSS animations
  - waiting for fonts to load...
  - fonts loaded
  - captured a stable screenshot
  - 54704 pixels (ratio 0.06 of all image pixels) are different.

```

# Page snapshot

```yaml
- generic [ref=e4]:
  - banner [ref=e5]:
    - generic [ref=e6]:
      - button "選單" [ref=e7] [cursor=pointer]:
        - generic [ref=e8]: ☰
      - link "JR Jig Record 回首頁" [ref=e10] [cursor=pointer]:
        - /url: /search
        - generic [ref=e11]: JR
        - generic [ref=e12]:
          - strong [ref=e13]: Jig Record
          - generic [ref=e14]: 回首頁
      - generic [ref=e15]: VISUAL
    - button "收／退料" [ref=e17] [cursor=pointer]
    - region "UI 介面" [ref=e19]:
      - tablist "切換 Workspace 或 Form UI" [ref=e21]:
        - tab [selected] [ref=e22] [cursor=pointer]:
          - strong [ref=e23]: Workspace UI
        - tab [ref=e24] [cursor=pointer]:
          - strong [ref=e25]: Form UI
      - generic [ref=e28]:
        - generic [ref=e29]: 預設
        - combobox "登入後預設介面" [ref=e30] [cursor=pointer]:
          - option "Workspace UI" [selected]
          - option "Form UI"
  - main [ref=e31]:
    - region "Workspace UI 系統介面" [ref=e32]:
      - region "現場工作台收退料總檢視" [ref=e33]:
        - generic [ref=e34]:
          - complementary "現場工作台總檢視導覽" [ref=e35]:
            - generic [ref=e37]:
              - generic [ref=e38]: 現場工作台
              - heading "收退料總檢視" [level=2] [ref=e39]
            - tablist "工作台作業模式" [ref=e40]:
              - tab "收料／退料" [ref=e41] [cursor=pointer]
              - tab "查詢治具" [ref=e42] [cursor=pointer]
              - tab "查詢機種" [ref=e43] [cursor=pointer]
              - tab "收／退料總檢視" [selected] [ref=e44] [cursor=pointer]
          - main [ref=e45]:
            - generic [ref=e46]:
              - generic [ref=e47]:
                - generic [ref=e48]: 庫存作業
                - heading "收退料總檢視" [level=2] [ref=e49]
              - generic [ref=e50]: VISUAL
            - region "收退料總檢視結果表格" [ref=e55]:
              - generic [ref=e56]:
                - generic [ref=e57]:
                  - strong [ref=e58]: "60"
                  - generic [ref=e59]: 筆資料
                - generic [ref=e60]:
                  - button "匯出篩選結果" [ref=e61] [cursor=pointer]
                  - generic [ref=e62]:
                    - text: 每頁
                    - combobox "每頁" [ref=e63]:
                      - option "50" [selected]
                      - option "100"
              - table [ref=e65]:
                - rowgroup [ref=e66]:
                  - row [ref=e67]:
                    - columnheader "類型" [ref=e68]
                    - columnheader "單號" [ref=e69]
                    - columnheader "治具編號" [ref=e70]
                    - columnheader "來源" [ref=e71]
                    - columnheader "datecode/編號" [ref=e72]
                    - columnheader "數量" [ref=e73]
                    - columnheader "操作人員" [ref=e74]
                    - columnheader "日期" [ref=e75]
                    - columnheader "備註" [ref=e76]
                - rowgroup [ref=e77]:
                  - row [ref=e78]:
                    - cell "退料" [ref=e79]
                    - cell "VIS-0001" [ref=e81]
                    - cell "FX-001" [ref=e82]
                    - cell "自購" [ref=e83]
                    - cell "2200" [ref=e84]
                    - cell "1" [ref=e85]
                    - cell "Operator A" [ref=e86]
                    - cell "2026-08-25" [ref=e87]
                    - cell [ref=e88]:
                      - button "Visual regression fixtur…" [ref=e89] [cursor=pointer]
                  - row [ref=e90]:
                    - cell "收料" [ref=e91]
                    - cell "VIS-0002" [ref=e93]
                    - cell "FX-002" [ref=e94]
                    - cell "客供" [ref=e95]
                    - cell "2201" [ref=e96]
                    - cell "2" [ref=e97]
                    - cell "Operator B" [ref=e98]
                    - cell "2026-08-24" [ref=e99]
                    - cell "-" [ref=e100]
                  - row [ref=e101]:
                    - cell "收料" [ref=e102]
                    - cell "VIS-0003" [ref=e104]
                    - cell "FX-003" [ref=e105]
                    - cell "客供" [ref=e106]
                    - cell "2202" [ref=e107]
                    - cell "3" [ref=e108]
                    - cell "Operator A" [ref=e109]
                    - cell "2026-08-23" [ref=e110]
                    - cell "-" [ref=e111]
                  - row [ref=e112]:
                    - cell "收料" [ref=e113]
                    - cell "VIS-0004" [ref=e115]
                    - cell "FX-004" [ref=e116]
                    - cell "自購" [ref=e117]
                    - cell "2203" [ref=e118]
                    - cell "4" [ref=e119]
                    - cell "Operator B" [ref=e120]
                    - cell "2026-08-22" [ref=e121]
                    - cell "-" [ref=e122]
                  - row [ref=e123]:
                    - cell "退料" [ref=e124]
                    - cell "VIS-0005" [ref=e126]
                    - cell "FX-005" [ref=e127]
                    - cell "客供" [ref=e128]
                    - cell "2204" [ref=e129]
                    - cell "5" [ref=e130]
                    - cell "Operator A" [ref=e131]
                    - cell "2026-08-21" [ref=e132]
                    - cell "-" [ref=e133]
                  - row [ref=e134]:
                    - cell "收料" [ref=e135]
                    - cell "VIS-0006" [ref=e137]
                    - cell "FX-006" [ref=e138]
                    - cell "客供" [ref=e139]
                    - cell "2205" [ref=e140]
                    - cell "6" [ref=e141]
                    - cell "Operator B" [ref=e142]
                    - cell "2026-08-25" [ref=e143]
                    - cell "-" [ref=e144]
                  - row [ref=e145]:
                    - cell "收料" [ref=e146]
                    - cell "VIS-0007" [ref=e148]
                    - cell "FX-007" [ref=e149]
                    - cell "自購" [ref=e150]
                    - cell "2206" [ref=e151]
                    - cell "7" [ref=e152]
                    - cell "Operator A" [ref=e153]
                    - cell "2026-08-24" [ref=e154]
                    - cell "-" [ref=e155]
                  - row [ref=e156]:
                    - cell "收料" [ref=e157]
                    - cell "VIS-0008" [ref=e159]
                    - cell "FX-008" [ref=e160]
                    - cell "客供" [ref=e161]
                    - cell "2207" [ref=e162]
                    - cell "8" [ref=e163]
                    - cell "Operator B" [ref=e164]
                    - cell "2026-08-23" [ref=e165]
                    - cell "-" [ref=e166]
                  - row [ref=e167]:
                    - cell "退料" [ref=e168]
                    - cell "VIS-0009" [ref=e170]
                    - cell "FX-001" [ref=e171]
                    - cell "客供" [ref=e172]
                    - cell "2208" [ref=e173]
                    - cell "9" [ref=e174]
                    - cell "Operator A" [ref=e175]
                    - cell "2026-08-22" [ref=e176]
                    - cell "-" [ref=e177]
                  - row [ref=e178]:
                    - cell "收料" [ref=e179]
                    - cell "VIS-0010" [ref=e181]
                    - cell "FX-002" [ref=e182]
                    - cell "自購" [ref=e183]
                    - cell "2209" [ref=e184]
                    - cell "1" [ref=e185]
                    - cell "Operator B" [ref=e186]
                    - cell "2026-08-21" [ref=e187]
                    - cell "-" [ref=e188]
                  - row [ref=e189]:
                    - cell "收料" [ref=e190]
                    - cell "VIS-0011" [ref=e192]
                    - cell "FX-003" [ref=e193]
                    - cell "客供" [ref=e194]
                    - cell "2210" [ref=e195]
                    - cell "2" [ref=e196]
                    - cell "Operator A" [ref=e197]
                    - cell "2026-08-25" [ref=e198]
                    - cell "-" [ref=e199]
                  - row [ref=e200]:
                    - cell "收料" [ref=e201]
                    - cell "VIS-0012" [ref=e203]
                    - cell "FX-004" [ref=e204]
                    - cell "客供" [ref=e205]
                    - cell "2211" [ref=e206]
                    - cell "3" [ref=e207]
                    - cell "Operator B" [ref=e208]
                    - cell "2026-08-24" [ref=e209]
                    - cell "-" [ref=e210]
                  - row [ref=e211]:
                    - cell "退料" [ref=e212]
                    - cell "VIS-0013" [ref=e214]
                    - cell "FX-005" [ref=e215]
                    - cell "自購" [ref=e216]
                    - cell "2212" [ref=e217]
                    - cell "4" [ref=e218]
                    - cell "Operator A" [ref=e219]
                    - cell "2026-08-23" [ref=e220]
                    - cell "-" [ref=e221]
                  - row [ref=e222]:
                    - cell "收料" [ref=e223]
                    - cell "VIS-0014" [ref=e225]
                    - cell "FX-006" [ref=e226]
                    - cell "客供" [ref=e227]
                    - cell "2213" [ref=e228]
                    - cell "5" [ref=e229]
                    - cell "Operator B" [ref=e230]
                    - cell "2026-08-22" [ref=e231]
                    - cell "-" [ref=e232]
                  - row [ref=e233]:
                    - cell "收料" [ref=e234]
                    - cell "VIS-0015" [ref=e236]
                    - cell "FX-007" [ref=e237]
                    - cell "客供" [ref=e238]
                    - cell "2214" [ref=e239]
                    - cell "6" [ref=e240]
                    - cell "Operator A" [ref=e241]
                    - cell "2026-08-21" [ref=e242]
                    - cell "-" [ref=e243]
                  - row [ref=e244]:
                    - cell "收料" [ref=e245]
                    - cell "VIS-0016" [ref=e247]
                    - cell "FX-008" [ref=e248]
                    - cell "自購" [ref=e249]
                    - cell "2215" [ref=e250]
                    - cell "7" [ref=e251]
                    - cell "Operator B" [ref=e252]
                    - cell "2026-08-25" [ref=e253]
                    - cell "-" [ref=e254]
                  - row [ref=e255]:
                    - cell "退料" [ref=e256]
                    - cell "VIS-0017" [ref=e258]
                    - cell "FX-001" [ref=e259]
                    - cell "客供" [ref=e260]
                    - cell "2216" [ref=e261]
                    - cell "8" [ref=e262]
                    - cell "Operator A" [ref=e263]
                    - cell "2026-08-24" [ref=e264]
                    - cell "-" [ref=e265]
                  - row [ref=e266]:
                    - cell "收料" [ref=e267]
                    - cell "VIS-0018" [ref=e269]
                    - cell "FX-002" [ref=e270]
                    - cell "客供" [ref=e271]
                    - cell "2217" [ref=e272]
                    - cell "9" [ref=e273]
                    - cell "Operator B" [ref=e274]
                    - cell "2026-08-23" [ref=e275]
                    - cell "-" [ref=e276]
                  - row [ref=e277]:
                    - cell "收料" [ref=e278]
                    - cell "VIS-0019" [ref=e280]
                    - cell "FX-003" [ref=e281]
                    - cell "自購" [ref=e282]
                    - cell "2218" [ref=e283]
                    - cell "1" [ref=e284]
                    - cell "Operator A" [ref=e285]
                    - cell "2026-08-22" [ref=e286]
                    - cell "-" [ref=e287]
                  - row [ref=e288]:
                    - cell "收料" [ref=e289]
                    - cell "VIS-0020" [ref=e291]
                    - cell "FX-004" [ref=e292]
                    - cell "客供" [ref=e293]
                    - cell "2219" [ref=e294]
                    - cell "2" [ref=e295]
                    - cell "Operator B" [ref=e296]
                    - cell "2026-08-21" [ref=e297]
                    - cell "-" [ref=e298]
                  - row [ref=e299]:
                    - cell "退料" [ref=e300]
                    - cell "VIS-0021" [ref=e302]
                    - cell "FX-005" [ref=e303]
                    - cell "客供" [ref=e304]
                    - cell "2220" [ref=e305]
                    - cell "3" [ref=e306]
                    - cell "Operator A" [ref=e307]
                    - cell "2026-08-25" [ref=e308]
                    - cell "-" [ref=e309]
                  - row [ref=e310]:
                    - cell "收料" [ref=e311]
                    - cell "VIS-0022" [ref=e313]
                    - cell "FX-006" [ref=e314]
                    - cell "自購" [ref=e315]
                    - cell "2221" [ref=e316]
                    - cell "4" [ref=e317]
                    - cell "Operator B" [ref=e318]
                    - cell "2026-08-24" [ref=e319]
                    - cell "-" [ref=e320]
                  - row [ref=e321]:
                    - cell "收料" [ref=e322]
                    - cell "VIS-0023" [ref=e324]
                    - cell "FX-007" [ref=e325]
                    - cell "客供" [ref=e326]
                    - cell "2222" [ref=e327]
                    - cell "5" [ref=e328]
                    - cell "Operator A" [ref=e329]
                    - cell "2026-08-23" [ref=e330]
                    - cell "-" [ref=e331]
                  - row [ref=e332]:
                    - cell "收料" [ref=e333]
                    - cell "VIS-0024" [ref=e335]
                    - cell "FX-008" [ref=e336]
                    - cell "客供" [ref=e337]
                    - cell "2223" [ref=e338]
                    - cell "6" [ref=e339]
                    - cell "Operator B" [ref=e340]
                    - cell "2026-08-22" [ref=e341]
                    - cell "-" [ref=e342]
                  - row [ref=e343]:
                    - cell "退料" [ref=e344]
                    - cell "VIS-0025" [ref=e346]
                    - cell "FX-001" [ref=e347]
                    - cell "自購" [ref=e348]
                    - cell "2224" [ref=e349]
                    - cell "7" [ref=e350]
                    - cell "Operator A" [ref=e351]
                    - cell "2026-08-21" [ref=e352]
                    - cell "-" [ref=e353]
                  - row [ref=e354]:
                    - cell "收料" [ref=e355]
                    - cell "VIS-0026" [ref=e357]
                    - cell "FX-002" [ref=e358]
                    - cell "客供" [ref=e359]
                    - cell "2225" [ref=e360]
                    - cell "8" [ref=e361]
                    - cell "Operator B" [ref=e362]
                    - cell "2026-08-25" [ref=e363]
                    - cell "-" [ref=e364]
                  - row [ref=e365]:
                    - cell "收料" [ref=e366]
                    - cell "VIS-0027" [ref=e368]
                    - cell "FX-003" [ref=e369]
                    - cell "客供" [ref=e370]
                    - cell "2226" [ref=e371]
                    - cell "9" [ref=e372]
                    - cell "Operator A" [ref=e373]
                    - cell "2026-08-24" [ref=e374]
                    - cell "-" [ref=e375]
                  - row [ref=e376]:
                    - cell "收料" [ref=e377]
                    - cell "VIS-0028" [ref=e379]
                    - cell "FX-004" [ref=e380]
                    - cell "自購" [ref=e381]
                    - cell "2227" [ref=e382]
                    - cell "1" [ref=e383]
                    - cell "Operator B" [ref=e384]
                    - cell "2026-08-23" [ref=e385]
                    - cell "-" [ref=e386]
                  - row [ref=e387]:
                    - cell "退料" [ref=e388]
                    - cell "VIS-0029" [ref=e390]
                    - cell "FX-005" [ref=e391]
                    - cell "客供" [ref=e392]
                    - cell "2228" [ref=e393]
                    - cell "2" [ref=e394]
                    - cell "Operator A" [ref=e395]
                    - cell "2026-08-22" [ref=e396]
                    - cell "-" [ref=e397]
                  - row [ref=e398]:
                    - cell "收料" [ref=e399]
                    - cell "VIS-0030" [ref=e401]
                    - cell "FX-006" [ref=e402]
                    - cell "客供" [ref=e403]
                    - cell "2229" [ref=e404]
                    - cell "3" [ref=e405]
                    - cell "Operator B" [ref=e406]
                    - cell "2026-08-21" [ref=e407]
                    - cell "-" [ref=e408]
                  - row [ref=e409]:
                    - cell "收料" [ref=e410]
                    - cell "VIS-0031" [ref=e412]
                    - cell "FX-007" [ref=e413]
                    - cell "自購" [ref=e414]
                    - cell "2230" [ref=e415]
                    - cell "4" [ref=e416]
                    - cell "Operator A" [ref=e417]
                    - cell "2026-08-25" [ref=e418]
                    - cell "-" [ref=e419]
                  - row [ref=e420]:
                    - cell "收料" [ref=e421]
                    - cell "VIS-0032" [ref=e423]
                    - cell "FX-008" [ref=e424]
                    - cell "客供" [ref=e425]
                    - cell "2231" [ref=e426]
                    - cell "5" [ref=e427]
                    - cell "Operator B" [ref=e428]
                    - cell "2026-08-24" [ref=e429]
                    - cell "-" [ref=e430]
                  - row [ref=e431]:
                    - cell "退料" [ref=e432]
                    - cell "VIS-0033" [ref=e434]
                    - cell "FX-001" [ref=e435]
                    - cell "客供" [ref=e436]
                    - cell "2232" [ref=e437]
                    - cell "6" [ref=e438]
                    - cell "Operator A" [ref=e439]
                    - cell "2026-08-23" [ref=e440]
                    - cell "-" [ref=e441]
                  - row [ref=e442]:
                    - cell "收料" [ref=e443]
                    - cell "VIS-0034" [ref=e445]
                    - cell "FX-002" [ref=e446]
                    - cell "自購" [ref=e447]
                    - cell "2233" [ref=e448]
                    - cell "7" [ref=e449]
                    - cell "Operator B" [ref=e450]
                    - cell "2026-08-22" [ref=e451]
                    - cell "-" [ref=e452]
                  - row [ref=e453]:
                    - cell "收料" [ref=e454]
                    - cell "VIS-0035" [ref=e456]
                    - cell "FX-003" [ref=e457]
                    - cell "客供" [ref=e458]
                    - cell "2234" [ref=e459]
                    - cell "8" [ref=e460]
                    - cell "Operator A" [ref=e461]
                    - cell "2026-08-21" [ref=e462]
                    - cell "-" [ref=e463]
                  - row [ref=e464]:
                    - cell "收料" [ref=e465]
                    - cell "VIS-0036" [ref=e467]
                    - cell "FX-004" [ref=e468]
                    - cell "客供" [ref=e469]
                    - cell "2235" [ref=e470]
                    - cell "9" [ref=e471]
                    - cell "Operator B" [ref=e472]
                    - cell "2026-08-25" [ref=e473]
                    - cell "-" [ref=e474]
                  - row [ref=e475]:
                    - cell "退料" [ref=e476]
                    - cell "VIS-0037" [ref=e478]
                    - cell "FX-005" [ref=e479]
                    - cell "自購" [ref=e480]
                    - cell "2236" [ref=e481]
                    - cell "1" [ref=e482]
                    - cell "Operator A" [ref=e483]
                    - cell "2026-08-24" [ref=e484]
                    - cell "-" [ref=e485]
                  - row [ref=e486]:
                    - cell "收料" [ref=e487]
                    - cell "VIS-0038" [ref=e489]
                    - cell "FX-006" [ref=e490]
                    - cell "客供" [ref=e491]
                    - cell "2237" [ref=e492]
                    - cell "2" [ref=e493]
                    - cell "Operator B" [ref=e494]
                    - cell "2026-08-23" [ref=e495]
                    - cell "-" [ref=e496]
                  - row [ref=e497]:
                    - cell "收料" [ref=e498]
                    - cell "VIS-0039" [ref=e500]
                    - cell "FX-007" [ref=e501]
                    - cell "客供" [ref=e502]
                    - cell "2238" [ref=e503]
                    - cell "3" [ref=e504]
                    - cell "Operator A" [ref=e505]
                    - cell "2026-08-22" [ref=e506]
                    - cell "-" [ref=e507]
                  - row [ref=e508]:
                    - cell "收料" [ref=e509]
                    - cell "VIS-0040" [ref=e511]
                    - cell "FX-008" [ref=e512]
                    - cell "自購" [ref=e513]
                    - cell "2239" [ref=e514]
                    - cell "4" [ref=e515]
                    - cell "Operator B" [ref=e516]
                    - cell "2026-08-21" [ref=e517]
                    - cell "-" [ref=e518]
                  - row [ref=e519]:
                    - cell "退料" [ref=e520]
                    - cell "VIS-0041" [ref=e522]
                    - cell "FX-001" [ref=e523]
                    - cell "客供" [ref=e524]
                    - cell "2240" [ref=e525]
                    - cell "5" [ref=e526]
                    - cell "Operator A" [ref=e527]
                    - cell "2026-08-25" [ref=e528]
                    - cell "-" [ref=e529]
                  - row [ref=e530]:
                    - cell "收料" [ref=e531]
                    - cell "VIS-0042" [ref=e533]
                    - cell "FX-002" [ref=e534]
                    - cell "客供" [ref=e535]
                    - cell "2241" [ref=e536]
                    - cell "6" [ref=e537]
                    - cell "Operator B" [ref=e538]
                    - cell "2026-08-24" [ref=e539]
                    - cell "-" [ref=e540]
                  - row [ref=e541]:
                    - cell "收料" [ref=e542]
                    - cell "VIS-0043" [ref=e544]
                    - cell "FX-003" [ref=e545]
                    - cell "自購" [ref=e546]
                    - cell "2242" [ref=e547]
                    - cell "7" [ref=e548]
                    - cell "Operator A" [ref=e549]
                    - cell "2026-08-23" [ref=e550]
                    - cell "-" [ref=e551]
                  - row [ref=e552]:
                    - cell "收料" [ref=e553]
                    - cell "VIS-0044" [ref=e555]
                    - cell "FX-004" [ref=e556]
                    - cell "客供" [ref=e557]
                    - cell "2243" [ref=e558]
                    - cell "8" [ref=e559]
                    - cell "Operator B" [ref=e560]
                    - cell "2026-08-22" [ref=e561]
                    - cell "-" [ref=e562]
                  - row [ref=e563]:
                    - cell "退料" [ref=e564]
                    - cell "VIS-0045" [ref=e566]
                    - cell "FX-005" [ref=e567]
                    - cell "客供" [ref=e568]
                    - cell "2244" [ref=e569]
                    - cell "9" [ref=e570]
                    - cell "Operator A" [ref=e571]
                    - cell "2026-08-21" [ref=e572]
                    - cell "-" [ref=e573]
                  - row [ref=e574]:
                    - cell "收料" [ref=e575]
                    - cell "VIS-0046" [ref=e577]
                    - cell "FX-006" [ref=e578]
                    - cell "自購" [ref=e579]
                    - cell "2245" [ref=e580]
                    - cell "1" [ref=e581]
                    - cell "Operator B" [ref=e582]
                    - cell "2026-08-25" [ref=e583]
                    - cell "-" [ref=e584]
                  - row [ref=e585]:
                    - cell "收料" [ref=e586]
                    - cell "VIS-0047" [ref=e588]
                    - cell "FX-007" [ref=e589]
                    - cell "客供" [ref=e590]
                    - cell "2246" [ref=e591]
                    - cell "2" [ref=e592]
                    - cell "Operator A" [ref=e593]
                    - cell "2026-08-24" [ref=e594]
                    - cell "-" [ref=e595]
                  - row [ref=e596]:
                    - cell "收料" [ref=e597]
                    - cell "VIS-0048" [ref=e599]
                    - cell "FX-008" [ref=e600]
                    - cell "客供" [ref=e601]
                    - cell "2247" [ref=e602]
                    - cell "3" [ref=e603]
                    - cell "Operator B" [ref=e604]
                    - cell "2026-08-23" [ref=e605]
                    - cell "-" [ref=e606]
                  - row [ref=e607]:
                    - cell "退料" [ref=e608]
                    - cell "VIS-0049" [ref=e610]
                    - cell "FX-001" [ref=e611]
                    - cell "自購" [ref=e612]
                    - cell "2248" [ref=e613]
                    - cell "4" [ref=e614]
                    - cell "Operator A" [ref=e615]
                    - cell "2026-08-22" [ref=e616]
                    - cell "-" [ref=e617]
                  - row [ref=e618]:
                    - cell "收料" [ref=e619]
                    - cell "VIS-0050" [ref=e621]
                    - cell "FX-002" [ref=e622]
                    - cell "客供" [ref=e623]
                    - cell "2249" [ref=e624]
                    - cell "5" [ref=e625]
                    - cell "Operator B" [ref=e626]
                    - cell "2026-08-21" [ref=e627]
                    - cell "-" [ref=e628]
              - generic [ref=e629]:
                - button "上一頁" [disabled] [ref=e630]
                - generic [ref=e631]: 第 1 / 2 頁
                - button "下一頁" [ref=e632] [cursor=pointer]
          - complementary "工作台篩選與編輯工具" [ref=e633]:
            - generic [ref=e634]:
              - generic [ref=e635]:
                - generic [ref=e636]: 操作面板
                - heading "篩選條件" [level=2] [ref=e637]
              - button "收合篩選" [expanded] [ref=e638] [cursor=pointer]
            - region "收退料總檢視條件" [ref=e640]:
              - generic [ref=e641]:
                - generic [ref=e642]:
                  - strong [ref=e643]: 篩選條件
                  - generic [ref=e644]: 收退料總檢視｜依目前功能顯示適用欄位
                - generic [ref=e645]:
                  - button "重新整理" [ref=e646]
                  - button "重設" [ref=e647] [cursor=pointer]
                  - button "套用條件" [ref=e648] [cursor=pointer]
              - generic [ref=e649]:
                - generic [ref=e650]:
                  - generic [ref=e651]: 類型
                  - group "類型複選" [ref=e652]:
                    - generic "全部類型" [ref=e653] [cursor=pointer]
                - generic [ref=e657]:
                  - generic [ref=e658]: 來源
                  - group "來源複選" [ref=e659]:
                    - generic "全部來源" [ref=e660] [cursor=pointer]
                - generic [ref=e664]:
                  - generic [ref=e665]: 起始日期
                  - textbox "起始日期" [ref=e666]
                - generic [ref=e667]:
                  - generic [ref=e668]: 結束日期
                  - textbox "結束日期" [ref=e669]
                - generic [ref=e670]:
                  - generic [ref=e671]: 治具編號
                  - textbox "治具編號" [ref=e672]:
                    - /placeholder: 治具編號 / 名稱
                - generic [ref=e673]:
                  - generic [ref=e674]: 單號
                  - textbox "單號" [ref=e675]
                - generic [ref=e676]:
                  - generic [ref=e677]: datecode/編號
                  - textbox "datecode/編號" [ref=e678]
                - generic [ref=e679]:
                  - generic [ref=e680]: 操作人員
                  - textbox "操作人員" [ref=e681]
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