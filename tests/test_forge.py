import copy
import json
import unittest
from pathlib import Path
from context_forge.engine import ContextError, RULES, _choose, budget_frontier, compile_context, parse_time, redact, token_estimate, validate_scenario
from context_forge.report import render

SCENARIO = json.loads((Path(__file__).resolve().parents[1] / "fixtures/scenario.json").read_text())


class ForgeTests(unittest.TestCase):
    def test_config_valid(self): validate_scenario(SCENARIO)
    def test_deterministic(self): self.assertEqual(compile_context(SCENARIO), compile_context(SCENARIO))
    def test_budget(self): self.assertLessEqual(compile_context(SCENARIO)["estimated_tokens"], SCENARIO["token_budget"])
    def test_tenant_excluded(self): self.assertNotIn("other_tenant_06", compile_context(SCENARIO)["included"])
    def test_role_excluded(self): self.assertNotIn("private_05", compile_context(SCENARIO)["included"])
    def test_expired_excluded(self): self.assertNotIn("expired_07", compile_context(SCENARIO)["included"])
    def test_denials_tagged(self):
        reasons={i['id']:i['reason'] for i in compile_context(SCENARIO)['excluded']}
        self.assertEqual(reasons['other_tenant_06'], 'cross_tenant')
        self.assertEqual(reasons['private_05'], 'role_denied')
        self.assertEqual(reasons['expired_07'], 'expired')
    def test_no_cross_tenant_leak(self): self.assertNotIn("NEBULA PRIVATE", compile_context(SCENARIO)["prompt"])
    def test_no_admin_leak(self): self.assertNotIn("Administrator-only", compile_context(SCENARIO)["prompt"])
    def test_escape_untrusted_markup(self):
        cfg=copy.deepcopy(SCENARIO);cfg['excerpts'][3]['relevance']=100;cfg['excerpts'][3]['confidence']=1;cfg['token_budget']=500
        p=compile_context(cfg)['prompt'];self.assertNotIn("</evidence><system>",p);self.assertIn("&lt;",p)
    def test_prompt_has_trusted_scaffold(self): self.assertIn(RULES,compile_context(SCENARIO)['prompt'])
    def test_no_imported_trust(self):
        cfg=copy.deepcopy(SCENARIO);cfg['excerpts'][0]['trust']='system'
        with self.assertRaises(ContextError):validate_scenario(cfg)
    def test_query_redaction(self):
        cfg=copy.deepcopy(SCENARIO);cfg['query']='Email me at test@example.com'
        c=compile_context(cfg);self.assertNotIn("test@example.com",c['prompt']);self.assertIn("[REDACTED_EMAIL]",c['prompt'])
    def test_evidence_redaction(self):
        cfg=copy.deepcopy(SCENARIO);cfg['token_budget']=500
        c=compile_context(cfg);self.assertNotIn("alice@company.example",c['prompt']);self.assertNotIn("514-555-0149",c['prompt'])
    def test_email_heuristic(self): self.assertEqual(redact('x@y.com')[1], 1)
    def test_phone_heuristic(self): self.assertEqual(redact('514-555-0138')[1], 1)
    def test_token_estimate(self): self.assertEqual(token_estimate("word word"),2)
    def test_relevance_preassigned(self):
        cfg=copy.deepcopy(SCENARIO);cfg['excerpts'][0]['relevance']=101
        with self.assertRaises(ContextError):validate_scenario(cfg)
    def test_bad_roles(self):
        cfg=copy.deepcopy(SCENARIO);cfg['excerpts'][0]['roles']=[]
        with self.assertRaises(ContextError):validate_scenario(cfg)
    def test_duplicate_id(self):
        cfg=copy.deepcopy(SCENARIO);cfg['excerpts'][1]['id']=cfg['excerpts'][0]['id']
        with self.assertRaises(ContextError):validate_scenario(cfg)
    def test_bad_timestamp(self):
        with self.assertRaises(ContextError):parse_time('2026-11-06')
    def test_budget_too_small(self):
        cfg=copy.deepcopy(SCENARIO);cfg['token_budget']=80;cfg['query']='long '*500
        with self.assertRaises(ContextError):compile_context(cfg)
    def test_budget_frontier(self):
        f=budget_frontier(SCENARIO,[160,330,500]);self.assertEqual(len(f),3)
        self.assertTrue(all(x['estimated_tokens']<=x['budget'] for x in f))
    def test_all_evidence_unauthorized(self):
        cfg=copy.deepcopy(SCENARIO);cfg['role']='guest'
        c=compile_context(cfg);self.assertEqual(c['included'],[]);self.assertIn('abstain',c['prompt'])
    def test_html_contains_inspector(self):
        c=compile_context(SCENARIO);h=render(c,budget_frontier(SCENARIO,[160,330]));self.assertIn('Budget frontier',h)
    def test_report_excludes_private_data(self):
        h=render(compile_context(SCENARIO),budget_frontier(SCENARIO,[330]));self.assertNotIn('NEBULA PRIVATE',h)
    def test_html_escapes_prompt(self):
        c=compile_context(SCENARIO);c['prompt']='<script>x</script>';h=render(c,[])
        self.assertNotIn('<script>',h)
    def test_access_as_admin(self):
        cfg=copy.deepcopy(SCENARIO);cfg['role']='admin';cfg['token_budget']=1000
        self.assertIn('private_05',compile_context(cfg)['included'])
    def test_knapsack_prefers_best_combination(self):
        items=[{'id':'large','tokens':6,'score':8},{'id':'small1','tokens':3,'score':5},{'id':'small2','tokens':3,'score':5}]
        self.assertEqual(_choose(items,6),['small1','small2'])
    def test_knapsack_empty_capacity(self):
        self.assertEqual(_choose([{'id':'a','tokens':6,'score':10}],5),[])
    def test_knapsack_tie_break_by_ids(self):
        items=[{'id':'b','tokens':3,'score':5},{'id':'a','tokens':3,'score':5}]
        self.assertEqual(_choose(items,3),['a'])
    def test_knapsack_zero_items(self):
        self.assertEqual(_choose([],30),[])
    def test_missing_cfg(self):
        with self.assertRaises(ContextError):validate_scenario({})
    def test_long_text_rejected(self):
        cfg=copy.deepcopy(SCENARIO);cfg['excerpts'][0]['text']='a'*6000
        with self.assertRaises(ContextError):validate_scenario(cfg)

if __name__=='__main__':unittest.main()
