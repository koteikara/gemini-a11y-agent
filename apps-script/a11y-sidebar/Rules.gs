/**
 * Rule definitions derived from a11y_agent/rules/a11y_hybrid_detect_fix.jsonl.
 * The extra fields support sidebar ordering, target counting, and review UX.
 */
var A11Y_SIDEBAR_RULES = [
  {id:'HTML-R-08',label:'日付・時刻・曜日表記の確認',category:'html',targetSelector:'body',defaultEnabled:true,executionMode:'detect-only',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'detect'},
  {id:'HTML-R-15',label:'table caption不足',category:'table',targetSelector:'table',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'low',mvp:'implemented'},
  {id:'HTML-R-16',label:'rowspan/colspanを含む複雑表',category:'table',targetSelector:'table',defaultEnabled:true,executionMode:'detect-only',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'high',mvp:'detect'},
  {id:'HTML-W-02',label:'レイアウトtable疑い',category:'table',targetSelector:'table',defaultEnabled:true,executionMode:'detect-only',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'high',mvp:'detect'},
  {id:'HTML-R-21',label:'矢印・装飾記号の確認',category:'html',targetSelector:'body',defaultEnabled:true,executionMode:'detect-only',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'detect'},
  {id:'LINK-R-02',label:'曖昧リンク文言',category:'link',targetSelector:'a',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'implemented'},
  {id:'LINK-R-03',label:'リンク切れチェック',category:'link',targetSelector:'a',defaultEnabled:false,executionMode:'not-implemented',requiresLlm:false,requiresNetwork:true,requiresReview:true,risk:'medium',mvp:'not-implemented'},
  {id:'LINK-R-04',label:'メールアドレスリンク確認',category:'link',targetSelector:'a',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'implemented'},
  {id:'LINK-R-06',label:'文章中の内部リンク分離',category:'link',targetSelector:'a',defaultEnabled:true,executionMode:'detect-only',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'detect'},
  {id:'LINK-R-08',label:'別ページfragmentリンク',category:'link',targetSelector:'a',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'low',mvp:'implemented'},
  {id:'LINK-R-09',label:'ページ内fragmentリンクのid確認',category:'link',targetSelector:'a',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'low',mvp:'implemented'},
  {id:'IMG-R-05',label:'リンク画像のalt確認',category:'image',targetSelector:'a img',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'implemented'},
  {id:'IMG-W-01',label:'画像alt生成支援',category:'image',targetSelector:'img',defaultEnabled:true,executionMode:'manual-llm',requiresLlm:true,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'manual-llm'},
  {id:'IMG-W-02',label:'YouTube iframe title補完',category:'iframe',targetSelector:'iframe',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'low',mvp:'implemented'},
  {id:'IMG-R-09',label:'画像ファイルへの拡大リンク確認',category:'image',targetSelector:'a',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'medium',mvp:'implemented'},
  {id:'SKIP-04',label:'末尾署名・問い合わせブロック候補',category:'skip',targetSelector:'body',defaultEnabled:true,executionMode:'review-candidate',requiresLlm:false,requiresNetwork:false,requiresReview:true,risk:'high',mvp:'implemented'}
];
