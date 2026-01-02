"""
STEP NEXT-73R: Store API Router

GET /store/proposal-detail/{proposal_detail_ref}
GET /store/evidence/{evidence_ref}
POST /store/evidence/batch
"""

from flask import Blueprint, jsonify, request
from apps.api.store_loader import get_proposal_detail, get_evidence, batch_get_evidence

store_bp = Blueprint('store', __name__, url_prefix='/store')


@store_bp.route('/proposal-detail/<path:ref>', methods=['GET'])
def get_proposal_detail_endpoint(ref: str):
    """
    GET /store/proposal-detail/PD:samsung:A4200_1

    Returns:
        200: {proposal_detail_ref, insurer, coverage_code, doc_type, page, benefit_description_text, hash}
        404: {error: "Not found"}
    """
    record = get_proposal_detail(ref)
    if record is None:
        return jsonify({'error': 'Proposal detail not found', 'ref': ref}), 404

    return jsonify(record), 200


@store_bp.route('/evidence/<path:ref>', methods=['GET'])
def get_evidence_endpoint(ref: str):
    """
    GET /store/evidence/EV:samsung:A4200_1:01

    Returns:
        200: {evidence_ref, insurer, coverage_code, doc_type, page, snippet, match_keyword, hash}
        404: {error: "Not found"}
    """
    record = get_evidence(ref)
    if record is None:
        return jsonify({'error': 'Evidence not found', 'ref': ref}), 404

    return jsonify(record), 200


@store_bp.route('/evidence/batch', methods=['POST'])
def batch_get_evidence_endpoint():
    """
    POST /store/evidence/batch
    Body: {"refs": ["EV:samsung:A4200_1:01", "EV:samsung:A4200_1:02"]}

    Returns:
        200: {
            "EV:samsung:A4200_1:01": {evidence_ref, ...},
            "EV:samsung:A4200_1:02": {evidence_ref, ...}
        }
    """
    data = request.get_json()
    if not data or 'refs' not in data:
        return jsonify({'error': 'Missing "refs" in request body'}), 400

    refs = data['refs']
    if not isinstance(refs, list):
        return jsonify({'error': '"refs" must be a list'}), 400

    result = batch_get_evidence(refs)
    return jsonify(result), 200
