function like_comment(comment_id) {
    fetch(`/comment/${comment_id}/like/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`like_count_${comment_id}`).innerText = data.like_count;
        } else {
            console.error('Error:', data.error);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}
function like_post(post_id) {
    fetch(`/post/${post_id}/like/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById(`like_count_${post_id}`).innerText = data.like_count;
        } else {
            console.error('Error:', data.error);
        }
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}