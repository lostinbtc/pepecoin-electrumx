"""Resume only an owned, stopped test DB with the exact originally tested image."""
import check_electrum as check

def inputs():
    owner = 'pep-index-test-123456789a'
    previous = {'full_chain': True, 'image_id': 'sha256:test', 'fresh_database': True,
                'container': owner, 'volume': owner + '-data'}
    return [previous, {'phase': 'stopped'}, 'sha256:test',
            {'Labels': {'io.pepecoin.test': owner}}, '']

def rejected(args):
    try:
        check.validate_resume(*args)
    except ValueError:
        return
    raise AssertionError('Unsafe resume was accepted')

def test_owned_stopped_same_image_is_allowed():
    args = inputs()
    assert check.validate_resume(*args) == (args[0]['volume'], args[0]['container'])

def test_different_image_is_rejected():
    args = inputs(); args[2] = 'sha256:different'; rejected(args)

def test_active_run_is_rejected():
    args = inputs(); args[1]['phase'] = 'indexing'; rejected(args)

def test_non_test_volume_is_rejected():
    args = inputs(); args[0]['volume'] = 'production-data'; rejected(args)

def test_wrong_label_is_rejected():
    args = inputs(); args[3]['Labels'] = {}; rejected(args)

def test_attached_container_is_rejected():
    args = inputs(); args[4] = 'existing-container'; rejected(args)

def test_unverified_origin_is_rejected():
    args = inputs(); args[0]['fresh_database'] = False; rejected(args)

def test_operator_cancellation_is_not_a_connection_error():
    assert not isinstance(check.TestStopped(), Exception)
    assert not isinstance(check.TestStopped(), OSError)
