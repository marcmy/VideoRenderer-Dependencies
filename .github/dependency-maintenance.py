"""Fast dependency-repository contracts. No runtime downloads or publishing."""
import argparse
import copy
import re
import unittest
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'marcmy/VideoRenderer'
REPOSITORY = SOURCE + '-Dependencies'
SHA = re.compile(r'[0-9a-f]{40}')
ACTIONS = {'actions/checkout', 'actions/setup-python', 'actions/upload-artifact', 'actions/download-artifact'}


class UniqueLoader(yaml.BaseLoader):
    def construct_mapping(self, node, deep=False):
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if key in mapping:
                raise ValueError('Duplicate YAML key: ' + str(key))
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check_actions(document):
    require(document.get('permissions') == {'contents': 'read'}, 'Workflow must default to read-only contents')
    for name, job in document['jobs'].items():
        if 'uses' in job:
            continue
        for step in job.get('steps', []):
            if 'uses' not in step:
                continue
            owner, revision = step['uses'].rsplit('@', 1)
            require(owner in ACTIONS and SHA.fullmatch(revision), 'External actions require reviewed full SHA pins')
            if owner == 'actions/checkout':
                require(step.get('with', {}).get('persist-credentials') == 'false', 'Checkout must not persist credentials')


def check_publisher(document):
    check_actions(document)
    require(set(document.get('on', {})) == {'workflow_dispatch'}, 'Publication must remain manual')
    jobs = document['jobs']
    require(set(jobs) == {'plan', 'runtime', 'models', 'maxine', 'publish'}, 'Unexpected publication job')
    plan = jobs['plan']
    source_steps = [step for step in plan['steps'] if step.get('id') == 'source']
    require(len(source_steps) == 1, 'Missing source approval gate')
    gate = source_steps[0]
    approved = gate['env']['APPROVED_SOURCE_REF']
    require(SHA.fullmatch(approved), 'Approved source must be a literal full SHA')
    expected = ("github.repository == '" + REPOSITORY + "' && (github.ref == 'refs/heads/main' || "
                "startsWith(github.ref, 'refs/tags/dependency-source-" + approved + "-'))")
    require(plan.get('if') == expected, 'Publication context is not bound to the approved source')
    require(gate['env']['SOURCE_REF'] == '${{ inputs.source_ref }}', 'Dispatch must be checked as data')
    require(gate.get('run') == 'python tools/Dev/dependencies.py approve-source --source-ref "$SOURCE_REF" --approved-ref "$APPROVED_SOURCE_REF"', 'Missing exact source check')
    require(plan['steps'].index(gate) < next(i for i, step in enumerate(plan['steps']) if step.get('id') == 'plan'), 'Approval must precede planning')
    for name, job in jobs.items():
        require(job.get('permissions', document['permissions']) == {'contents': 'write' if name == 'publish' else 'read'}, 'Only publisher may write repository contents')
        if 'uses' in job:
            builder = 'rife-runtime' if name == 'runtime' else 'rife-model'
            require(job['uses'] == SOURCE + '/.github/workflows/' + builder + '.yml@' + approved, 'Builder definition differs from approved source')
            require(job['with'] == {'source_repository': SOURCE, 'source_ref': approved}, 'Builder source is not approved')
            require(job.get('needs') == 'plan', 'Builder must depend on approval')
        else:
            for step in job.get('steps', []):
                if step.get('uses', '').startswith('actions/checkout@'):
                    require(step['with'].get('repository') == SOURCE and step['with'].get('ref') == approved, 'Checkout source must be the literal approved commit')
    require(jobs['maxine'].get('needs') == 'plan', 'Maxine must depend on approval')
    require(set(jobs['publish']['needs']) == {'plan', 'runtime', 'models', 'maxine'}, 'Publisher must depend on approved builders')
    require(jobs['publish']['if'].startswith("always() && needs.plan.outputs.needed == 'true'"), 'No publication without successful planning')


class ContractTests(unittest.TestCase):
    publisher = None

    def test_valid_configuration(self):
        check_publisher(self.publisher)

    def test_reject_broken_boundaries(self):
        def checkout_input(doc): doc['jobs']['plan']['steps'][0]['with']['ref'] = '${{ inputs.source_ref }}'
        def builder_mismatch(doc): doc['jobs']['runtime']['uses'] = SOURCE + '/.github/workflows/rife-runtime.yml@' + 'b'*40
        def builder_input(doc): doc['jobs']['models']['with']['source_ref'] = '${{ inputs.source_ref }}'
        def extra_write(doc): doc['jobs']['plan']['permissions'] = {'contents': 'write'}
        def persisted_token(doc): doc['jobs']['maxine']['steps'][0]['with']['persist-credentials'] = 'true'
        def floating_action(doc): doc['jobs']['plan']['steps'][0]['uses'] = 'actions/checkout@v7'
        def automatic_publish(doc): doc['on']['pull_request'] = ''
        def weak_context(doc): doc['jobs']['plan']['if'] += ' || true'
        def no_gate(doc): doc['jobs']['plan']['steps'][1]['run'] = 'echo approved'
        for mutation in [checkout_input, builder_mismatch, builder_input, extra_write, persisted_token,
                         floating_action, automatic_publish, weak_context, no_gate]:
            with self.subTest(mutation=mutation.__name__):
                document = copy.deepcopy(self.publisher)
                mutation(document)
                with self.assertRaises(ValueError): check_publisher(document)

    def test_reject_duplicate_security_keys(self):
        with self.assertRaises(ValueError):
            yaml.load('permissions: {contents: read, contents: write}', Loader=UniqueLoader)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    documents = {path.name: yaml.load(path.read_text(), Loader=UniqueLoader)
                 for path in sorted((ROOT/'.github/workflows').glob('*.yml'))}
    require(set(documents) == {'publish.yml', 'validate.yml'}, 'Unexpected workflow requires explicit maintenance review')
    check_publisher(documents['publish.yml'])
    check_actions(documents['validate.yml'])
    validation = documents['validate.yml']
    require(set(validation['on']) == {'pull_request', 'push', 'workflow_dispatch'}, 'Missing maintenance validation triggers')
    require(set(validation['jobs']) == {'validate'}, 'Unexpected validation job')
    require(validation['jobs']['validate'].get('permissions', validation['permissions']) == {'contents': 'read'}, 'Validation must remain unprivileged')
    updates = yaml.load((ROOT/'.github/dependabot.yml').read_text(), Loader=UniqueLoader)['updates']
    actions = next(update for update in updates if update['package-ecosystem'] == 'github-actions')
    require(any(item['dependency-name'] == SOURCE + '*' for item in actions.get('ignore', [])), 'Dependabot must preserve approved renderer workflow pins')
    print('Workflow syntax, action pins, source binding and permissions verified.')
    if args.self_test:
        ContractTests.publisher = documents['publish.yml']
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ContractTests))
        if not result.wasSuccessful(): raise SystemExit(1)


if __name__ == '__main__':
    main()
